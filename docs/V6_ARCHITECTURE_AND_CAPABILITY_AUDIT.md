# PromptIQ V6 — Architecture and Capability Audit
## Forensic Inspection, Operational Reality, Technical Gaps & V6 Engineering Strategy

**Auditor**: Principal Systems Architect, Staff Backend Engineer & Independent Quality Auditor  
**Milestone**: V6 Engineering Initiation  
**Date**: 2026-11-22  
**Baseline Git Commit**: `14c6bbb`  
**Current Release Candidate**: `v4.1.0-rc1`  
**Audit Scope**: Full Backend, Intelligence Engine, Model Gateway, Distributed Reliability, Research Engine, Compilers, Evaluation Lab, and Surfaces  

---

## 1. Executive Forensic Summary

This audit assesses the actual state of the PromptIQ codebase following the completion of milestone `v4.1.0-rc1`. 

While previous hardening cycles established strong structural safety (264 hermetic pytest tests passing, clean Ruff/Bandit/pip-audit, Alembic migration 0003, and 5-layer database persistence validation), a deep inspection of the source code reveals significant boundaries between:
1. **Deterministic heuristic scaffolding** vs **Genuine autonomous intelligence**.
2. **Sequential task loops** vs **True hierarchical DAG task planning and decomposition**.
3. **Simulated search and deterministic mock fallbacks** vs **Live external evidence synthesis**.
4. **In-process asyncio concurrency testing** vs **Actual multi-process distributed execution**.
5. **In-memory CLI/SDK test harnesses** vs **Real OS subprocess and network execution**.

This document categorizes every component into its actual operational reality, identifies technical gaps, and defines the exact architectural enhancements required for **PromptIQ V6**.

---

## 2. Component-by-Component Forensic Audit

### 2.1 Adaptive Discovery & Intent Capture
- **Source Files**: `promptiq/discovery/adaptive.py`, `task_paths.py`, `task_registry.py`, `software_stages.py`
- **Execution Mode**: **Hybrid (75% Deterministic Heuristics / 25% LLM Inference)**
- **Operational Reality**:
  - The discovery process categorizes questions by slicing static lists defined in `task_paths.py` (`[:1]` for quick, `[:3]` for guided).
  - Contradiction detection (`detect_contradictions`) is an array of hardcoded string/regex checks (e.g. searching for `"no frontend"` vs `"react"`, or `"zero-price"` vs `"aws fargate"`).
  - Inferred requirements are generated via a call to `inference_gateway.generate`, but when running with mock models (`promptiq-mock-v1`), it falls back to fixed dictionary templates.
- **Shortcomings & Gaps**:
  - **No Information-Sufficiency Assessment**: The engine does not compute whether enough high-impact information has been gathered to stop discovery early or when to ask high-decision-value clarifying questions.
  - **Static Follow-Ups**: The next question does not dynamically adapt based on nuances in the user's previous answer; it merely steps through predefined stages.
  - **Lack of Confidence/Impact Scoring**: Unknowns are treated equally rather than distinguishing low-impact aesthetic preferences from critical architectural requirements.
- **V6 Action Required**: Implement an explicit `InformationSufficiencyEvaluator`, decision-value question ranking, dynamic intent taxonomy (explicit, strongly implied, reasonable assumption, unverified assumption, unknown), and impact assessment.

---

### 2.2 Project Constitution & Change-Impact Engine
- **Source Files**: `promptiq/models/constitution.py`, `promptiq/services/constitution_service.py`, `promptiq/schemas/constitution.py`
- **Execution Mode**: **Deterministic Relational Storage**
- **Operational Reality**:
  - Persists JSON columns (`goals`, `scope`, `requirements`, `technical_direction`, `ux_specs`) in SQLite/Postgres.
  - Updates increment the integer `version` field atomically and retain audit records.
- **Shortcomings & Gaps**:
  - **No Change-Impact Analysis**: When a constraint changes (e.g., changing target compiler or architectural style), previously generated PPS specifications, artifacts, and test lab suites are not flagged as stale or invalid.
  - **Unenforced Requirement Dependency Graphs**: Requirements track `depends_on`, but circular dependency checks and topological validation are not enforced on update.
- **V6 Action Required**: Implement a formal `ConstitutionChangeImpactAnalyzer` that computes downstream artifact/specification invalidations and validates requirement dependency DAGs.

---

### 2.3 Prompt Specification (PPS v2) & Target Compilers
- **Source Files**: `promptiq/compiler/pps.py`, `target_compiler.py`, `promptiq/adapters/*`
- **Execution Mode**: **Deterministic Code Transformation**
- **Operational Reality**:
  - `PPSBuilder` deterministically maps Constitution records to typed Pydantic schemas (`PromptSpecSchema`).
  - Target adapters (`antigravity.py`, `claude.py`, `cursor.py`, `codex.py`, `gemini.py`, `raw_prompt.py`) use string templates to generate markdown and rule files.
- **Shortcomings & Gaps**:
  - **Instruction-to-Requirement Traceability**: Individual generated markdown sections do not maintain machine-readable provenance links back to originating `REQ-xxx` IDs.
  - **Generic Compiler Guidance**: Adapters format standard boilerplate rather than optimizing prompt structure for task-family specific constraints (e.g. data analysis SQL validation vs agent tool restrictions).
  - **Static Package Validation**: Compilers validate file existence but do not verify syntax conformance against official target schema specifications.
- **V6 Action Required**: Introduce fine-grained instruction requirement annotations, target-specific official convention linters, and task-family compiler specialization.

---

### 2.4 Orchestration & Workflow Planning
- **Source Files**: `promptiq/orchestrator/task_graph.py`, `collaboration.py`, `router.py`
- **Execution Mode**: **Mixed (Pipeline-specific in collaboration.py / Stub in task_graph.py)**
- **Operational Reality**:
  - `SpecialistOrchestrator` in `task_graph.py` is a 56-line sequential loop with two hardcoded specialists.
  - `MultiModelCollaborationPipeline` in `collaboration.py` is a specialized 5-stage linear flow (Stage A Generation -> Stage B Verification -> Stage C Autopsy -> Stage D Revision -> Stage E Final Verification) built specifically for backend architecture prompts.
- **Shortcomings & Gaps**:
  - **No General-Purpose DAG Planning Engine**: The system lacks a generic task-decomposition engine that can take any user objective, construct a dependency graph of subtasks, identify parallelizable steps, execute them with checkpoints, and handle dynamic retries.
  - **No Universal Execution-Intelligence Loop**: The system lacks a unified implementation of the canonical pattern: **Understand → Discover → Specify → Plan → Execute → Inspect → Critique → Revise → Verify → Deliver → Remember**.
- **V6 Action Required**: Implement a general-purpose `TaskPlanningEngine` supporting hierarchical DAG decomposition, critical path analysis, and a unified execution loop with structured checkpointing.

---

### 2.5 Prompt Autopsy & Adversarial Critique
- **Source Files**: `promptiq/critic/autopsy.py`, `tests/fixtures/autopsy_golden_dataset.json`
- **Execution Mode**: **Deterministic Regular Expressions + Optional LLM Pass**
- **Operational Reality**:
  - Evaluates 21 categories using pre-compiled regular expressions (e.g. `VAGUE_TERMS`, `UNSAFE_PERMISSIONS`, `INJECTION_RISK`).
  - An optional second pass calls `inference_gateway.generate` for semantic critique.
  - Golden benchmark dataset contains 25 prompts in `tests/fixtures/autopsy_golden_dataset.json`.
- **Shortcomings & Gaps**:
  - **Context-Insensitive Diagnostics**: Regular expressions flag terms without considering task context (e.g., flagging a creative writing prompt for missing JSON schemas or error handling).
  - **Small Synthetic Benchmark**: 25 prompts do not provide statistical significance or held-out test splits.
  - **No Precision/Recall/F1 Reporting**: Autopsy tests assert pass/fail rather than measuring true positives, false positives, true negatives, and false negatives.
- **V6 Action Required**: Introduce task-family context filters to Autopsy heuristics, expand the benchmark suite to at least 100 prompts across all 10 task families with held-out splits, and compute formal precision/recall/F1 metrics.

---

### 2.6 Research Engine & Evidence Graph
- **Source Files**: `promptiq/research/engine.py`, `promptiq/research/connectors/live_search.py`
- **Execution Mode**: **Deterministic Retrieval with Simulated Fallback**
- **Operational Reality**:
  - `LiveWebSearchConnector` contains genuine socket-pinned HTTP retrieval with 31 SSRF vectors blocked.
  - When live network queries are unavailable or in CI, it delegates to deterministic simulated citations with `provenance="simulated"`.
- **Shortcomings & Gaps**:
  - **Coarse Claim Extraction**: Claims are generated from basic sentence splitting rather than semantic entity-relationship extraction.
  - **No Exact Excerpt Offsets**: Evidence citations do not record character start/end offsets within source text.
  - **No Contradiction Resolution**: The engine detects disagreements between sources but does not analyze confidence or explain conflicting evidence.
- **V6 Action Required**: Implement exact character-offset citation verification, cross-source contradiction analysis, and a structured evidence graph.

---

### 2.7 Prompt Test Lab & Evaluation
- **Source Files**: `promptiq/eval/test_lab.py`, `tournament.py`
- **Execution Mode**: **Deterministic String Assertions + Model-as-Judge**
- **Operational Reality**:
  - Evaluates packages using `contains`, `not_contains`, `regex`, and `model_judge` assertions.
- **Shortcomings & Gaps**:
  - **Limited Test Coverage**: Most scenarios run only 1 or 2 test cases.
  - **No Distinct Test Tiers**: Test results do not clearly differentiate deterministic assertions, schema validation, model judgments, and live external execution.
  - **No Standardized 10-Family Benchmark**: Lacks a formal benchmark covering 10 diverse test cases per task family.
- **V6 Action Required**: Implement a comprehensive Test Lab benchmark suite with 10 test cases per task family (100 total evaluation cases) with separated evaluation tiers.

---

### 2.8 Persistent Project Memory & Context Intelligence
- **Source Files**: `promptiq/memory/context_compiler.py`, `checkpoint.py`, `promptiq/models/memory.py`
- **Execution Mode**: **Deterministic Priority Packing**
- **Operational Reality**:
  - `ContextCompiler` packs goals, constraints, and requirements into markdown blocks, filtering by priority `P0`, `P1`, `P2` and token budgets.
- **Shortcomings & Gaps**:
  - **No Memory Conflict Resolution**: If a user updates a requirement that conflicts with an earlier decision, the compiler does not flag the supersession.
  - **No Structured Memory Types**: Memory is stored primarily as requirements rather than distinct types (active decisions, accepted risks, open questions, historical decisions).
- **V6 Action Required**: Implement typed memory entities (`ActiveDecision`, `AcceptedRisk`, `OpenQuestion`, `SupersededDecision`) with conflict detection and automated supersession handling.

---

### 2.9 Distributed Reliability & Concurrency
- **Source Files**: `promptiq/services/job_service.py`, `promptiq/gateway/governor.py`, `promptiq/models/job.py`, `governor.py`
- **Execution Mode**: **Asyncio Database Transactions**
- **Operational Reality**:
  - `WorkflowJobService` manages worker leases (`lease_owner`, `lease_expires_at`), heartbeats, and progress checkpoints.
  - `CapacityGovernor` supports two-phase database quota reservations (`reserve_quota_db`, `commit_quota_db`).
- **Shortcomings & Gaps**:
  - **Multi-Process Testing Was Simulated in Asyncio**: All previous concurrency tests ran within a single Python process using `asyncio.gather`. Genuine independent OS processes (`multiprocessing.Process` or `subprocess.Popen`) were not tested.
  - **PostgreSQL Live Status Was NOT TESTED**: The test suite ran solely against SQLite.
- **V6 Action Required**: Author true multi-process test suites spawning separate OS worker processes competing for the same database job leases and quota reservations; attempt local PostgreSQL spin-up or document exact blocking constraints.

---

### 2.10 Multi-Surface Integrations (REST, MCP, CLI, Telegram, SDK)
- **Source Files**: `promptiq/api/`, `promptiq/mcp/`, `promptiq/cli/`, `promptiq/telegram/`, `promptiq/sdk/`
- **Execution Mode**: **Mixed (FastAPI / Click / Python Client)**
- **Operational Reality**:
  - REST API has 36 endpoints with JWT auth, rotating refresh tokens, and durable jobs.
  - Telegram bot has database-backed webhook deduplication with savepoints.
- **Shortcomings & Gaps**:
  - **CLI Tests Used In-Memory CliRunner**: Did not test actual OS process exit codes, stdout/stderr streams, or subprocess execution.
  - **SDK Tested In-Memory Mock Transport**: Did not test against an active HTTP server socket.
  - **SSE Streaming Tested Via Mock Generator**: Did not verify client reconnection, `Last-Event-ID` resumption, and heartbeat interval enforcement over real HTTP.
- **V6 Action Required**: Add real subprocess tests for the CLI (`subprocess.run`), test the Python SDK against a live ephemeral test server, and verify SSE streaming protocols end-to-end.

---

## 3. Forensic Classification Matrix

| Capability | Actual Implementation Reality | V6 Action |
| :--- | :--- | :--- |
| **Intent Understanding** | Keyword extraction + regex contradiction checks | Implement `IntentReasoningEngine` with confidence & impact assessment |
| **Adaptive Discovery** | Predefined question arrays sliced by depth | Implement `AdaptiveDiscoveryEngine` with information-sufficiency stop conditions |
| **Project Constitution** | Versioned JSON tables | Add `ConstitutionChangeImpactAnalyzer` and DAG dependency validation |
| **PPS Specification** | Pydantic data modeling | Add requirement traceability annotations and schema versioning |
| **Target Compilation** | Jinja/format string templates | Add official target syntax validation and task-specialized templates |
| **Task Planning** | Linear 5-stage collaboration pipeline | Implement general-purpose hierarchical `TaskPlanningEngine` with DAG dependencies |
| **Prompt Autopsy** | 21 regex patterns + 25-prompt benchmark | Add task-aware diagnostic filtering and a 100+ prompt benchmark with held-out split |
| **Research Engine** | Socket-pinned HTTP + simulated fallback | Add character-offset citation verification and contradiction analysis |
| **Test Lab** | Deterministic string assertions | Build 100-case evaluation suite (10 per family) with separated evaluation tiers |
| **Project Memory** | Token-budgeted requirement packing | Add typed memory records with conflict resolution and supersession tracking |
| **Distributed Jobs** | Asyncio DB lease updates | Add true OS multi-process stress tests with worker crash recovery |
| **Quota Governance** | DB two-phase reservations | Add multi-process reservation race condition tests and fail-closed validation |
| **CLI & SDK** | In-memory Click / httpx tests | Add real OS subprocess execution tests and live socket SDK tests |
| **PostgreSQL** | Dialect compatibility in code, live untested | Attempt local container/service verification or confirm honest blocked state |

---

## 4. Conclusion & V6 Engineering Strategy

PromptIQ's backend foundations are remarkably solid and secure. However, to evolve from a "hardened release candidate" to an **exceptionally intelligent, reliable AI workflow platform**, we must replace static scaffolds with dynamic, evidence-backed reasoning engines, build a true general-purpose task planner, expand evaluation benchmarks to statistically meaningful sizes, and prove distributed concurrency using real multi-process execution.

This audit establishes the roadmap for the V6 implementation cycle.
