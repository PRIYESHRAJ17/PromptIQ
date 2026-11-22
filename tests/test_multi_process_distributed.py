"""Multi-process distributed concurrency and reliability tests using separate OS processes."""

import multiprocessing
import os
import sqlite3
import tempfile
import time
import uuid


def _worker_claim_job(
    db_path: str, job_id: str, worker_id: str, result_queue: multiprocessing.Queue
):
    """Child OS process worker attempting to atomically claim a job."""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout = 5000;")

        # Check current lease
        cursor.execute(
            "SELECT status, lease_owner, lease_expires_at, fencing_token FROM workflow_jobs WHERE id = ?",
            (job_id,),
        )
        row = cursor.fetchone()
        if not row:
            result_queue.put((worker_id, False, "Job not found", 0))
            conn.close()
            return

        status, lease_owner, lease_expires_at, fencing_token = row
        now_ts = time.time()

        if status in ("QUEUED", "RUNNING") and (
            lease_owner is None or lease_expires_at is None or lease_expires_at < now_ts
        ):
            # Attempt atomic update with optimistic locking
            new_fencing = (fencing_token or 0) + 1
            new_exp = now_ts + 30
            cursor.execute(
                """
                UPDATE workflow_jobs
                SET status = 'RUNNING', lease_owner = ?, lease_expires_at = ?, fencing_token = ?
                WHERE id = ? AND (lease_owner IS ? OR lease_expires_at < ? OR status = 'QUEUED')
                """,
                (worker_id, new_exp, new_fencing, job_id, lease_owner, now_ts),
            )
            conn.commit()
            if cursor.rowcount > 0:
                result_queue.put((worker_id, True, "Lease acquired", new_fencing))
            else:
                result_queue.put((worker_id, False, "Lost race to another process", fencing_token))
        else:
            result_queue.put(
                (worker_id, False, f"Job already leased to {lease_owner}", fencing_token)
            )

        conn.close()
    except Exception as exc:
        result_queue.put((worker_id, False, str(exc), 0))


def _worker_reserve_quota(
    db_path: str, model_id: str, tokens: int, worker_id: str, result_queue: multiprocessing.Queue
):
    """Child OS process worker attempting to atomically reserve quota against shared ledger."""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout = 5000;")

        # Read limit and current usage
        cursor.execute(
            "SELECT SUM(allocated_tokens) FROM quota_reservations WHERE model_id = ? AND status = 'HELD'",
            (model_id,),
        )
        row = cursor.fetchone()
        current_reserved = row[0] or 0

        MAX_TOKEN_LIMIT = 5000
        if current_reserved + tokens <= MAX_TOKEN_LIMIT:
            res_id = f"res-{uuid.uuid4().hex[:8]}"
            cursor.execute(
                """
                INSERT INTO quota_reservations (id, reservation_id, model_id, allocated_tokens, status, expires_at)
                VALUES (?, ?, ?, ?, 'HELD', ?)
                """,
                (res_id, res_id, model_id, tokens, time.time() + 60),
            )
            conn.commit()
            result_queue.put((worker_id, True, tokens))
        else:
            result_queue.put((worker_id, False, 0))

        conn.close()
    except Exception as exc:
        result_queue.put((worker_id, False, str(exc)))


def test_multiprocess_job_claim_mutual_exclusion():
    """Verifies that when two independent OS processes compete to claim the same job, exactly one wins."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            CREATE TABLE workflow_jobs (
                id TEXT PRIMARY KEY,
                status TEXT,
                lease_owner TEXT,
                lease_expires_at REAL,
                fencing_token INTEGER DEFAULT 0
            )
        """)
        job_id = f"job-{uuid.uuid4()}"
        cursor.execute(
            "INSERT INTO workflow_jobs (id, status, lease_owner, lease_expires_at, fencing_token) VALUES (?, 'QUEUED', NULL, NULL, 0)",
            (job_id,),
        )
        conn.commit()
        conn.close()

        # Spawn 2 OS processes
        q = multiprocessing.Queue()
        p1 = multiprocessing.Process(
            target=_worker_claim_job, args=(db_path, job_id, "worker-OS-1", q)
        )
        p2 = multiprocessing.Process(
            target=_worker_claim_job, args=(db_path, job_id, "worker-OS-2", q)
        )

        p1.start()
        p2.start()

        p1.join(timeout=10)
        p2.join(timeout=10)

        results = []
        while not q.empty():
            results.append(q.get())

        assert len(results) == 2
        successes = [r for r in results if r[1] is True]
        failures = [r for r in results if r[1] is False]

        assert len(successes) == 1, f"Expected exactly 1 winner, got: {results}"
        assert len(failures) == 1, f"Expected exactly 1 loser, got: {results}"
        assert successes[0][3] == 1  # Fencing token incremented to 1
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass


def test_multiprocess_quota_concurrency_hard_limit():
    """Verifies that 4 concurrent OS processes reserving tokens cannot exceed assigned limit."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            CREATE TABLE quota_reservations (
                id TEXT PRIMARY KEY,
                reservation_id TEXT,
                model_id TEXT,
                allocated_tokens INTEGER,
                status TEXT,
                expires_at REAL
            )
        """)
        conn.commit()
        conn.close()

        # Each worker asks for 2000 tokens against a 5000 limit -> at most 2 can succeed
        q = multiprocessing.Queue()
        workers = [
            multiprocessing.Process(
                target=_worker_reserve_quota, args=(db_path, "gpt-oss-120b", 2000, f"w-{i}", q)
            )
            for i in range(4)
        ]

        for w in workers:
            w.start()
        for w in workers:
            w.join(timeout=10)

        results = []
        while not q.empty():
            results.append(q.get())

        successes = [r for r in results if r[1] is True]
        total_reserved = sum(r[2] for r in successes)

        assert total_reserved <= 5000, f"Overbooking occurred! Total reserved: {total_reserved}"
        assert len(successes) <= 2, f"More than 2 workers succeeded: {len(successes)}"
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
