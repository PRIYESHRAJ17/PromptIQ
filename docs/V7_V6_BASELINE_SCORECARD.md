# PROMPTIQ V7 — V6 BASELINE SCORECARD (OFFICIAL INDEPENDENT SCORES)

## 1. Executive Summary

This scorecard records the authoritative V6 baseline evaluation scores. These scores serve as the starting point for the V7 milestone. No self-inflated scores are permitted; all evaluations are grounded in demonstrated behavior and independently reproducible evidence.

---

## 2. Baseline Scores Table (0–10 Scale)

| Evaluation Dimension | V6 Baseline Score | Baseline Status | Key Deficiencies & Missing Capabilities |
|---|---:|---|---|
| **Intent Understanding** | **7.0** | Partially Demonstrated | Keyword/regex intent extraction; lacks complex multi-objective resolution, implicit requirement handling, and constraint tradeoff analysis. |
| **Uncertainty & Truth Tracking** | **6.8** | Heuristic | Epistemic states and confidence tiers defined in schema, but not statistically calibrated against ground-truth datasets. |
| **Adaptive Discovery** | **7.2** | Structured | Sufficiency evaluator ranks questions by decision value, but question sequencing is rarely conditioned dynamically on prior answers. |
| **Prompt Engineering & Compilation** | **7.0** | Syntactic | Native packaging exists for 5 targets, but lacks target-specific execution testing within real target CLI/agent environments. |
| **Planning & Task Decomposition** | **7.5** | Isolated | `TaskPlanningEngine` creates DAGs and critical paths in unit tests, but is disconnected from the main collaboration runtime. |
| **Agentic Execution & Autonomy** | **5.8** | Low / Fragmented | No continuous observe-decide-act loop; no tool execution registry; no dynamic plan adaptation when observations fail. |
| **Task-Family Specialization** | **6.5** | Metadata Only | 10 task families registered in registry, but actual runtime execution follows identical pipeline paths with minor prompt differences. |
| **Research & Evidence Intelligence** | **5.5** | Sandboxed | Character-offset citations verified in fixtures; no independent claim-to-source entailment verifier; live search sandboxed. |
| **Prompt Autopsy** | **6.5** | Overfitted | Evaluated against only 30 benchmark cases; high scores reflect small fixture dataset rather than robust generalized defect detection. |
| **Test Lab** | **6.5** | Basic Rubrics | Evaluated on 100 cases, but heavily weighted toward simple deterministic regex and schema checks rather than deep model-judged rubrics. |
| **Persistent Memory** | **6.0** | Storage Only | Decision records and checkpoints stored in DB, but multi-session retrieval lacks contradiction resolution and context budgeting. |
| **Model Gateway & Routing** | **5.5** | Single-Model Bound | Capability-aware routing defined, but runtime is effectively bound to single zero-price provider with multi-pass simulation. |
| **Distributed Reliability** | **7.8** | Strong Unit Evidence | Atomic leasing, optimistic fencing tokens, and hard quota limits verified via multi-process tests. |
| **Database Readiness** | **5.0** | Blocked Daemon | Migrations 0001-0003 and PostgreSQL 16 dialect compilation verified; live PostgreSQL daemon is `BLOCKED` due to workstation environment. |
| **Security & Privacy** | **7.0** | Code Hardened | 31/31 SSRF vectors blocked; tenant isolation enforced; Bandit clean; lacks formal multi-tenant penetration testing. |
| **API & Integration Readiness** | **6.8** | Contract Ready | FastAPI REST, MCP, CLI subprocess, and Telegram bots verified; lacks SSE resume event replay and live webhook verification. |
| **Code Quality & Test Discipline** | **8.0** | High Standard | 280 passing tests, 80% statement coverage, clean Ruff/Bandit/pip-audit/compileall. |
| **Cloud Production Readiness** | **1.0** | Explicitly Blocked | Cardless ₹0 compute cannot be guaranteed without risking billing overages or violating zero-price invariant (`BLOCKED`). |
| **Overall Baseline Assessment** | **6.7 / 10** | Baseline Release Candidate | Substantial architecture, but substantial gap between design and autonomous agent execution. |

---

## 3. High-Priority V7 Focus Areas

To move PromptIQ from a 6.7 baseline to an 8.2+ platform, the V7 engineering effort must focus on the lowest-scoring, highest-impact operational deficiencies:

1. **Agentic Execution & Autonomy** (5.8 $\to$ 8.0+): Build the authoritative observe-decide-act loop and tool execution engine.
2. **Research & Evidence Intelligence** (5.5 $\to$ 7.5+): Implement independent claim-to-source entailment verification and expand benchmark to 100 cases.
3. **Model Gateway & Multi-Model** (5.5 $\to$ 7.5+): Transparent single-model multi-pass labeling, task budgeting, and gateway resilience.
4. **Persistent Memory** (6.0 $\to$ 8.0+): Multi-session continuity, decision superseding, and context token budgeting.
5. **Prompt Autopsy** (6.5 $\to$ 8.0+): Expand benchmark to 300 diverse prompts (dev, val, held-out) across all 21 failure modes.
6. **Task-Family Specialization** (6.5 $\to$ 8.0+): Distinct tool sets, DAG execution paths, and 200 diverse scenarios (10 dev + 10 held-out per family).
