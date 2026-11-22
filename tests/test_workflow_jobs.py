"""Tests for WorkflowJobService and workflow job execution lifecycle."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.exceptions import ConflictError, TenantIsolationError
from promptiq.services.job_service import WorkflowJobService


@pytest.mark.asyncio
async def test_job_create_and_idempotency(db_session: AsyncSession) -> None:
    user_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())
    idem_key = f"job-key-{uuid.uuid4()}"

    # Create first time
    job1 = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="PROMPT_COMPILATION",
        idempotency_key=idem_key,
        initial_stage="task_discovery",
        checkpoint_data={"step": 1},
    )
    assert job1.id is not None
    assert job1.status == "QUEUED"
    assert job1.current_stage == "task_discovery"

    # Create second time with same idempotency key and workspace -> should return existing
    job2 = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="PROMPT_COMPILATION",
        idempotency_key=idem_key,
    )
    assert job2.id == job1.id

    # Create with same idempotency key in different workspace -> should raise TenantIsolationError
    other_ws = str(uuid.uuid4())
    with pytest.raises(TenantIsolationError):
        await WorkflowJobService.create_job(
            db=db_session,
            user_id=user_id,
            workspace_id=other_ws,
            operation_type="PROMPT_COMPILATION",
            idempotency_key=idem_key,
        )


@pytest.mark.asyncio
async def test_job_lease_acquisition_and_progress(db_session: AsyncSession) -> None:
    user_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())

    job = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="RESEARCH_WORKFLOW",
    )

    # Worker 1 acquires lease
    acquired = await WorkflowJobService.acquire_lease(
        db=db_session,
        job_id=job.id,
        worker_id="worker-A",
        lease_duration_seconds=30,
    )
    assert acquired is True
    assert job.status == "RUNNING"
    assert job.lease_owner == "worker-A"

    # Worker 2 attempts to acquire lease while worker-A holds valid lease
    conflict = await WorkflowJobService.acquire_lease(
        db=db_session,
        job_id=job.id,
        worker_id="worker-B",
        lease_duration_seconds=30,
    )
    assert conflict is False

    # Worker 1 updates progress
    updated = await WorkflowJobService.update_progress(
        db=db_session,
        job_id=job.id,
        stage="searching_sources",
        progress_percent=50,
        checkpoint={"query": "test query"},
        provenance_update={"worker": "worker-A"},
        lease_worker_id="worker-A",
    )
    assert updated.current_stage == "searching_sources"
    assert updated.progress_percent == 50
    assert updated.checkpoint_data["query"] == "test query"


@pytest.mark.asyncio
async def test_job_pause_resume_cancel_lifecycle(db_session: AsyncSession) -> None:
    user_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())

    job = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="AUTOPSY_EVALUATION",
    )

    # Pause job
    paused = await WorkflowJobService.pause_job(
        db=db_session,
        job_id=job.id,
        reason="Quota window saturated",
        checkpoint={"pause_step": "verification"},
    )
    assert paused.status == "PAUSED"
    assert paused.failure_reason == "Quota window saturated"
    assert paused.lease_owner is None

    # Resume job
    resumed = await WorkflowJobService.resume_job(
        db=db_session,
        job_id=job.id,
        user_id=user_id,
        workspace_id=ws_id,
    )
    assert resumed.status == "QUEUED"
    assert resumed.failure_reason is None

    # Cancel job
    cancelled = await WorkflowJobService.cancel_job(
        db=db_session,
        job_id=job.id,
        user_id=user_id,
        workspace_id=ws_id,
        reason="User requested abort",
    )
    assert cancelled.status == "CANCELLED"
    assert cancelled.failure_reason == "User requested abort"

    # Attempting to resume a cancelled job should raise ConflictError
    with pytest.raises(ConflictError):
        await WorkflowJobService.resume_job(
            db=db_session,
            job_id=job.id,
            user_id=user_id,
            workspace_id=ws_id,
        )


@pytest.mark.asyncio
async def test_job_failure_retry_and_stale_recovery(db_session: AsyncSession) -> None:
    user_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())

    job = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="CODE_COMPILATION",
    )
    job.max_retries = 2

    # First failure -> retry 1, status QUEUED
    f1 = await WorkflowJobService.fail_job(db=db_session, job_id=job.id, error_message="Network glitch")
    assert f1.status == "QUEUED"
    assert f1.retry_count == 1

    # Second failure -> retry 2, status QUEUED
    f2 = await WorkflowJobService.fail_job(db=db_session, job_id=job.id, error_message="Provider timeout")
    assert f2.status == "QUEUED"
    assert f2.retry_count == 2

    # Third failure -> reaches max_retries, status FAILED
    f3 = await WorkflowJobService.fail_job(db=db_session, job_id=job.id, error_message="Unrecoverable error")
    assert f3.status == "FAILED"

    # Test stale job recovery
    stale_job = await WorkflowJobService.create_job(
        db=db_session,
        user_id=user_id,
        workspace_id=ws_id,
        operation_type="STALE_JOB",
    )
    stale_job.status = "RUNNING"
    stale_job.lease_owner = "dead-worker"
    stale_job.lease_expires_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.flush()

    recovered = await WorkflowJobService.recover_stale_jobs(db=db_session, timeout_seconds=60)
    assert recovered >= 1

    reloaded = await WorkflowJobService.get_job(db=db_session, job_id=stale_job.id, workspace_id=ws_id)
    assert reloaded.status == "QUEUED"
    assert reloaded.lease_owner is None


@pytest.mark.asyncio
async def test_job_api_endpoints(client: AsyncClient) -> None:
    # Register and get auth headers
    user_email = f"job_api_{uuid.uuid4().hex[:6]}@promptiq.dev"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "JobPassword123!",
            "full_name": "Job User",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create job via API
    create_res = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "operation_type": "PROMPT_OPTIMIZATION",
            "initial_stage": "task_intake",
            "checkpoint_data": {"user_goal": "test prompt"},
        },
    )
    assert create_res.status_code == 201
    job_data = create_res.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"
    assert job_data["operation_type"] == "PROMPT_OPTIMIZATION"

    # 2. List jobs
    list_res = await client.get("/api/v1/jobs", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(j["id"] == job_id for j in items)

    # 3. Get single job
    get_res = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # 4. Cancel job
    cancel_res = await client.post(
        f"/api/v1/jobs/{job_id}/cancel",
        headers=headers,
        json={"reason": "User cancelled test job"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

