# PromptIQ — Quota Governance, Concurrency & Recovery Design

**Version**: 3.0.0  
**Updated**: 2026-11-22  
**Module Reference**: `promptiq/gateway/governor.py`, `promptiq/orchestrator/collaboration.py`, `tests/test_quota_reservation_transactions.py`

---

## 1. Executive Summary

PromptIQ operates strictly on **zero-cost provider tiers**. Free tiers are heavily rate-limited (e.g. GroqCloud GPT-OSS 120B is capped at 8,000 TPM and 30 RPM; Google Gemini 1.5 Pro is capped at 2 RPM and 32k TPM).

To operate reliably without exceeding provider limits or dropping workflows, PromptIQ implements:
1. **Durable, Cross-Process Quota Ledger**: File-locked atomic JSON ledger surviving CLI and API restarts.
2. **Two-Phase Quota Reservation Transactions**: Guarantees capacity before dispatching HTTP calls.
3. **Workflow State Checkpointing & Resumption**: Preserves partially completed multi-model workflows during rate-limit pauses, preventing duplicate token expenditure upon resumption.

---

## 2. Durable Cross-Process Quota Ledger Architecture

```
+-----------------------------------------------------------------------------------+
|                        CAPACITY GOVERNOR ARCHITECTURE                             |
+-----------------------------------------------------------------------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
                v                                                   v
   [FastAPI Background Worker]                             [PromptIQ CLI Process]
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v
                      [File Lock Mechanism (Cross-Process)]
                      - Windows: msvcrt.locking (LK_NBLCK)
                      - Unix/Linux: fcntl.flock (LOCK_EX)
                      - Retries: 5 attempts with jittered backoff
                                          |
                                          v
                              [data/quota_ledger.json]
                      - Rolling 60s Request Count (RPM)
                      - Rolling 60s Token Count (TPM)
                      - Rolling 24h Token Count (TPD)
                      - Reset Epoch Synchronized via Provider Headers
```

### 2.1 File Locking Implementation
Because PromptIQ is accessed across multiple decoupled surfaces (FastAPI server, independent CLI commands, background Celery/anyio tasks), in-memory counters cannot prevent cross-process quota exhaustion.

`promptiq/gateway/governor.py` implements OS-native atomic file locking:
```python
@contextmanager
def _acquire_ledger_lock(filepath: Path):
    with open(filepath, "r+") as f:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield f
        finally:
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

---

## 3. Two-Phase Quota Transactions

Every LLM inference request passes through a two-phase reservation protocol:

```
[Phase 1: Reserve]
  Client -> CapacityGovernor.reserve(model_id, estimated_tokens=4096)
  1. Acquire cross-process file lock on quota ledger.
  2. Prune expired entries from rolling 60s / 24h windows.
  3. Verify (current_rpm + 1 <= limit_rpm) and (current_tpm + estimated <= limit_tpm).
  4. If exceeded: compute sleep_until_reset and raise CapacityExhaustedError(retry_after).
  5. If permitted: record pending reservation with TTL (60s) and return reservation_id.
  6. Release file lock.

[Execution]
  Client dispatches HTTP request to Upstream Provider (e.g. GroqCloud).
  Captures: HTTP Status, completion tokens, prompt tokens, rate-limit headers.

[Phase 2: Commit or Rollback]
  Case A: HTTP 200 OK
    Client -> CapacityGovernor.commit(reservation_id, actual_prompt_tokens, actual_completion_tokens)
    - Re-acquires file lock.
    - Adjusts ledger: replaces estimated tokens with actual tokens.
    - Updates provider reset window from x-ratelimit-reset-* headers.
    - Releases file lock.

  Case B: HTTP 429 Rate Limit / HTTP 5xx / Network Error
    Client -> CapacityGovernor.release(reservation_id)
    - Re-acquires file lock.
    - Deletes reservation without counting consumed tokens.
    - Marks circuit breaker PAUSED if 429 received.
    - Releases file lock.
```

Verified in `tests/test_quota_reservation_transactions.py`.

---

## 4. Partial Multi-Model Collaboration Recovery

### 4.1 The Rate-Limit Problem in Multi-Model Workflows
A complete PromptIQ collaborative refinement workflow involves:
1. **Stage A (Orchestration)**: GPT-OSS 120B extracts requirements (~3,360 tokens).
2. **Stage B (Initial Generation)**: GPT-OSS 120B generates full architecture (~4,302 tokens).
3. **Stage C (Adversarial Critique)**: GPT-OSS 20B analyzes and identifies flaws (~4,242 tokens).
4. **Stage D (Deterministic Verification)**: Static code analysis & rubric check.
5. **Stage E (Revision)**: GPT-OSS 120B revises the architecture based on critique (~2,842 tokens).

Under GroqCloud's free tier, GPT-OSS 120B is subject to an **8,000 TPM rolling limit**. Stages A and B consume `3,360 + 4,302 = 7,662 tokens`, leaving only 338 tokens remaining. An immediate dispatch of Stage E inevitably triggers HTTP 429 Rate Limit.

### 4.2 State Preservation & Zero-Quota-Waste Resumption
PromptIQ does not abort or discard completed stages upon encountering a rate limit:
1. **Checkpointing**: Stages A, B, C, and D are committed to the project database and saved to `docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json`.
2. **Workflow Trace**: Contains `workflow_id`, provider request IDs (`req_01m7zssrj0ee28v1rdzv49pt8a`, `req_01m7zsszn3etavc26tspeb7jhr`, `req_01m7zst8fcerebw0z1p9a48vam`), and deterministic verification metrics.
3. **Resumption Command**:
   ```bash
   promptiq collaborate --resume --workflow-id 422f4399-c93f-439f-a7ef-bbf3149a4057
   ```
4. **Targeted Execution**:
   - The orchestrator detects that Stages A through D are already completed and verified.
   - It reads the persisted critic response directly from the checkpoint.
   - It queries the CapacityGovernor for the 120B rolling window reset timestamp.
   - Once reset, it dispatches **only Stage E (Revision)** (`req_01m7zvprh4ev9v7e67f2ypx2r7`).
   - Stages A and B are **never repeated**, conserving 7,662 tokens.
