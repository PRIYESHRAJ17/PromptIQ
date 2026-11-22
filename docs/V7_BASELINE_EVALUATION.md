# PROMPTIQ V7 — BASELINE EVALUATION REPORT (PRE-EXECUTION AUDIT)

## 1. Executive Summary

This document establishes the frozen, authoritative baseline of the PromptIQ repository prior to implementing the V7 milestone. In accordance with the V7 methodology, this baseline evaluation documents the actual operational reality, capabilities, limitations, and benchmark results of the V6 implementation (`00a9061`).

---

## 2. Technical Baseline Environment

| Environment Parameter | Baseline Value |
|---|---|
| **Baseline Git Commit** | `00a9061e23b82b21cd8f7a6cf0874b062d7dc502` |
| **Git Tag** | `v6-baseline` |
| **Branch** | `master` |
| **Python Runtime** | `3.13.14 (win32)` |
| **Primary Frameworks** | FastAPI 0.115.0, SQLAlchemy 2.0.30, Alembic 1.13.0, Pydantic 2.8.0 |
| **Testing Harness** | pytest 9.2.0, pytest-cov 7.1.0, pytest-asyncio 1.5.0 |
| **Code Quality Tools** | Ruff 0.6.0, Bandit 1.9.4, pip-audit 2.9.0 |
| **Database Dialects** | SQLite 3.x (`aiosqlite`) tested; PostgreSQL 16 dialect compiled |
| **Operating System** | Windows 11 (Developer Workstation) |

---

## 3. Test & Verification Baseline at `00a9061`

- **Automated Tests**: 280 passed in 27.18s (100% pass rate).
- **Statement Coverage**: 80% (8,967 statements scanned across `promptiq`).
- **Static Analysis**:
  - `ruff check .`: 0 errors.
  - `bandit -r promptiq`: 0 issues identified.
  - `pip-audit`: 0 known vulnerabilities.
  - `python -m compileall`: 0 compilation errors.
- **Multi-Process Concurrency**: Real OS child processes (`multiprocessing.Process`) verified atomic job leasing and quota hard-limit enforcement.
- **CLI Subprocess**: Verified via `subprocess.run` (exit code 0, help, status, quota, secret redaction).
- **Acceptance Scenario Runner**: 10 task families executed, 111/111 independent trace checks passed, 5/5 database persistence layers validated.

---

## 4. Architectural Capability vs. Operational Reality Audit

While V6 delivered substantial architectural code, an independent audit reveals significant operational gaps between what was architected and what was actually demonstrated in execution:

### 4.1 Orchestrator & Planner Gap
- **Architectural Status**: `TaskPlanningEngine` exists in `promptiq/orchestrator/planner.py` and creates subtask DAGs with dependencies and critical paths.
- **Operational Reality**: Normal user workflows in `promptiq/orchestrator/collaboration.py` and `promptiq/acceptance/runner.py` bypassed the planner entirely, executing hardcoded sequential steps (`Orchestrator` $\to$ `Generator` $\to$ `Critic` $\to$ `Reviser` $\to$ `Verifier`).
- **Missing Capability**: No dynamic subtask execution loop, no tool execution registry, no observation step, and no runtime plan adaptation based on tool outcomes.

### 4.2 Autonomous Agent Loop Gap
- **Architectural Status**: 11 stages defined as an enum (`ExecutionLoopStage`).
- **Operational Reality**: There was no active **Understand $\to$ Plan $\to$ Select Action $\to$ Check Permission $\to$ Execute $\to$ Observe $\to$ Evaluate $\to$ Update Plan** loop. The agent did not select tools, execute actions in an environment, or observe results.
- **Missing Capability**: Absence of a unified `ToolRegistry` with permission levels (`read_only`, `reversible_modification`, `external_communication`, `destructive`), timeouts, and retry policies.

### 4.3 Research & Evidence Grounding Gap
- **Architectural Status**: `EvidenceGraphBuilder` in `promptiq/research/evidence_graph.py` extracts character-offset citations and detects contradictions.
- **Operational Reality**: External live search remains sandboxed; claims are largely validated against pre-seeded fixtures or simulated fallback content rather than live web documents.
- **Missing Capability**: No independent claim-to-source verifier that evaluates whether an excerpt logically entails, contradicts, or fails to support a claim.

### 4.4 Autopsy & Benchmark Scope Gap
- **Architectural Status**: 21 failure modes defined with diagnostic schemas.
- **Operational Reality**: Benchmarked on a development split of 20 cases and a held-out split of 10 cases.
- **Missing Capability**: A dataset of 30 cases is insufficient to demonstrate generalizable prompt autopsy intelligence across 21 failure modes and 10 task families.

### 4.5 Task Family Specialization Gap
- **Architectural Status**: 10 task families registered in `TaskFamilyRegistry` with configuration metadata.
- **Operational Reality**: Workflows shared largely identical execution mechanics with differing text prompts rather than specialized tool execution, distinct verification rubrics, or dynamic failure recovery.

---

## 5. Environmental & Production Limitations

1. **Local PostgreSQL Live Connection**: `BLOCKED`. Port 5432 is closed (connection refused). Docker is not installed on this workstation.
2. **Cloud Production Deployment**: `BLOCKED`. Preserving the non-negotiable ₹0 zero-liability invariant prevents deploying to cloud platforms requiring credit cards or carrying usage overage risks.
3. **Live External Web Retrieval**: `SANDBOXED / SIMULATED`. No outbound internet access is permitted from this sandbox environment; all research occurs via local connectors and test fixtures.
