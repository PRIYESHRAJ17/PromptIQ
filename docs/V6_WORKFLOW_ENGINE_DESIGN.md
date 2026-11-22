# PROMPTIQ V6 — WORKFLOW ENGINE AND DISTRIBUTED ORCHESTRATION DESIGN

## Executive Overview

PromptIQ V6 formalizes workflow execution around a 11-stage universal bounded loop and a hierarchical Directed Acyclic Graph (DAG) task planning engine. Distributed execution guarantees at-least-once delivery, mutual exclusion via atomic database leases, optimistic fencing tokens, and automatic dead-letter queueing on retry exhaustion.

---

## 1. Universal Bounded Execution-Intelligence Loop

**Source**: `promptiq/orchestrator/planner.py` (`ExecutionLoopStage`)

PromptIQ enforces an 11-stage pipeline for all intelligent workflows:

```mermaid
flowchart LR
    A[Understand] --> B[Discover]
    B --> C[Specify]
    C --> D[Plan]
    D --> E[Execute]
    E --> F[Inspect]
    F --> G[Critique]
    G --> H[Revise]
    H --> I[Verify]
    I --> J[Deliver]
    J --> K[Remember]
```

1. **Understand**: Parse raw prompt/intent, separate primary from secondary objectives, identify non-negotiable invariants.
2. **Discover**: Evaluate information sufficiency; dynamically rank clarifying questions by decision value.
3. **Specify**: Generate typed PromptIQ Prompt Specification (PPS v2.0) with explicit requirement bindings.
4. **Plan**: Decompose into hierarchical subtasks with explicit dependencies and execution methods.
5. **Execute**: Route subtasks to specialized deterministic code, research retrieval, or hosted zero-price models.
6. **Inspect**: Perform structural and semantic validation of generated artifacts.
7. **Critique**: Subject outputs to adversarial Prompt Autopsy across 21 failure modes.
8. **Revise**: Targeted remediation of identified critical and high-severity findings.
9. **Verify**: Execute Test Lab test cases and assertion gates.
10. **Deliver**: Compile target-native instruction package with cryptographic content hashing.
11. **Remember**: Persist execution trace, decisions, accepted risks, and evidence into project memory.

---

## 2. Hierarchical DAG Task Planning Engine

**Source**: `promptiq/orchestrator/planner.py` (`TaskPlanningEngine`, `ExecutionPlan`, `SubtaskNode`)

### Execution Methods
Subtasks within an execution plan are assigned execution methods:
- `DETERMINISTIC_CODE`: Fast, reproducible, non-LLM computation (e.g. hashing, linting, graph validation).
- `MODEL_INFERENCE`: Centrally managed hosted zero-price LLM inference.
- `MULTI_MODEL_COLLABORATION`: Multi-turn debate, tournament, or peer review across distinct models.
- `RESEARCH_RETRIEVAL`: Controlled SSRF-protected external evidence collection.
- `VALIDATOR_VERIFICATION`: Assertions, schema validation, and benchmark scoring.

### Dependency Resolution
`get_executable_subtasks(plan)` computes the dynamic frontier of executable nodes whose prerequisite dependencies have all transitioned to `COMPLETED`. Cyclic dependencies are prohibited and checked at plan initialization.

---

## 3. Distributed Job Leasing and Mutual Exclusion

**Source**: `promptiq/models/job.py`, `promptiq/services/job_service.py`, `alembic/versions/b2c3d4e5f6a7_0003_add_workflow_jobs_and_auth_hardening.py`

### Database Schema Contract
The `workflow_jobs` table implements distributed leasing:
- `lease_owner` (String): Identifier of the active worker node/process holding the lease.
- `lease_expires_at` (Float/DateTime): Epoch timestamp after which the lease is considered expired.
- `fencing_token` (Integer): Monotonically increasing sequence number incremented on every lease acquisition.
- `retry_count` (Integer): Current failure count.
- `max_retries` (Integer): Maximum allowed retries before permanent dead-lettering.
- `status` (Enum): `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `DEAD_LETTER`.

### Atomic Lease Acquisition Query
```sql
UPDATE workflow_jobs
SET status = 'RUNNING',
    lease_owner = :worker_id,
    lease_expires_at = :new_expiry,
    fencing_token = fencing_token + 1
WHERE id = :job_id
  AND (status = 'QUEUED' OR lease_expires_at < :now OR lease_owner = :worker_id);
```

### Stale Worker Rejection
When a worker attempts to update job progress or complete a job, it must present its assigned `fencing_token`. If another worker reclaimed an expired lease in the interim, the fencing token will have been incremented, causing the stale worker's write to be rejected (`409 Conflict`), preventing split-brain state corruption.

### Dead-Letter Transition
When a job encounters a terminal error or exhausts its retry budget (`retry_count >= max_retries`), it transitions to `DEAD_LETTER` status with full stack trace and diagnostic context recorded in `error_details`.

---

## 4. Multi-Process Verification Evidence

**Source**: `tests/test_multi_process_distributed.py`

1. **Job Claim Race**:
   - 4 independent operating system processes (`multiprocessing.Process`) launched simultaneously to claim the exact same pending job.
   - Result: Exactly 1 process acquired the lease; 3 processes were cleanly rejected.
2. **Concurrent Quota Reservation**:
   - 4 independent processes raced to reserve 2,000 tokens each against a 5,000-token cap.
   - Result: Exactly 2 processes succeeded (4,000 tokens reserved); 2 processes were blocked when attempting to exceed the hard limit. Zero quota oversubscription occurred.
