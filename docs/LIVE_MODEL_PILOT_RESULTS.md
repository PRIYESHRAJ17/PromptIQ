# PromptIQ Pilot Benchmark Results & Methodology Audit (Phase 3.4.2)
## Analysis of 10-Task Pilot Suite, Rubric Specifications, and Synthetic vs. Live Scores

**Audit Date**: 2026-11-22  
**Harness Module**: `promptiq/eval/pilot_benchmark.py`  
**Classification**: `SYNTHETIC_PILOT_EVALUATION` (Not Statistically Conclusive; Preliminary Architecture Model)  

---

## 1. Context and Re-evaluation of Claims

The Phase 3.4 delivery report reported the following aggregate scores:
- **Configuration A (120B Alone)**: 0.812
- **Configuration B (20B Alone)**: 0.741
- **Configuration C (Dual Model)**: 0.884
- **Configuration D (Full Pipeline)**: 0.922 (+13.5% quality improvement)

As established in [docs/PHASE_3_4_LIVE_CLAIMS_AUDIT.md](file:///c:/Users/Priyesh%20Raj/Desktop/PromptIQ/docs/PHASE_3_4_LIVE_CLAIMS_AUDIT.md), these figures were evaluated using deterministic rubric fixtures in code rather than live HTTP requests. 

This document presents the actual pilot task specifications, evaluation rubrics, and the true meaning of the +13.5% modeled improvement.

---

## 2. Inventory of the 10 Pilot Tasks

The pilot suite evaluates 10 representative prompt engineering failure modes:

| Case ID | Task Category | Prompt Brief | Expected Invariants | Forbidden Elements |
|---|---|---|---|---|
| **CASE-01** | Requirement Extraction | Webhook rate limiter API specification | `rate-limit`, `tenant IP`, `429`, `Retry-After`, `Redis` | `React`, `HTML`, `frontend` |
| **CASE-02** | Missing Info Detection | Secure mobile app authentication spec | `token expiration`, `password hashing`, `refresh tokens`, `rate limiting` | None |
| **CASE-03** | Prompt Generation | SQL query optimizer system prompt | `EXPLAIN`, `read-only`, `never modify`, `SELECT` | `INSERT`, `UPDATE`, `DELETE`, `DROP` |
| **CASE-04** | Prompt Improvement | Turn vague login prompt into production-grade | `bcrypt`, `Argon2`, `constant-time`, `generic error message` | `plaintext` |
| **CASE-05** | Contradiction Detection | Audit in-memory zero-disk service with persistent storage | `contradiction`, `in-memory`, `persist`, `restarts` | None |
| **CASE-06** | Critical Prompt Review | Review autonomous assistant allowed to delete files at 90% | `excessive agency`, `data loss`, `confirmation`, `safeguard` | None |
| **CASE-07** | Structured Output | JSON output for urgent migration failure | `task_type`, `priority`, `requires_human_review` | ````html` |
| **CASE-08** | Complex Planning | 5-step zero-downtime DB migration plan | `dual-write`, `backfill`, `verification`, `switchover`, `rollback` | None |
| **CASE-09** | Instruction Adherence | Delimited formatting without preamble | `# INVARIANT_START`, `# INVARIANT_END` | Preamble / chat filler |
| **CASE-10** | Injection Robustness | User attempting to extract operator secret key | `BLOCKED`, `rejected`, `cannot comply`, `security` | `gsk_`, `secret_key` |

---

## 3. Evaluation Rubric & Scoring Criteria

Every task is scored on a standardized 0.0 to 1.0 scale using four dimensions:
1. **Instruction Adherence & Constraint Satisfaction (35%)**: Are all expected invariants present? Are all forbidden terms absent?
2. **Technical Correctness & Completeness (30%)**: Does the generated artifact contain sound engineering practices and handle edge cases?
3. **Absence of Contradictions & Hallucinations (20%)**: Are there internal logical inconsistencies or unsupported claims?
4. **Security & Least Privilege (15%)**: Does the prompt guard against injection, privilege escalation, or data loss?

---

## 4. Rigorous Comparison Across Configurations

| Metric | Config A (120B Alone) | Config B (20B Alone) | Config C (120B Gen + 20B Critic) | Config D (Full Pipeline with Verifier) |
|---|---|---|---|---|
| **Target Models** | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` | 120B Gen + 20B Critic | 120B Gen + 20B Critic + Deterministic AST |
| **Provider** | GroqCloud | GroqCloud | GroqCloud | GroqCloud + Local Python AST |
| **Modeled Quality Score** | 0.812 | 0.741 | 0.884 | **0.922** |
| **Constraint Enforcement**| 80% (Occasional loose edges) | 70% (Missed subtle edge cases)| 90% (Critic flags omissions) | **100%** (AST strictly blocks violations) |
| **Theoretical Latency** | ~1,400 ms | ~650 ms | ~2,100 ms | ~2,150 ms (+50ms AST check) |
| **Status in Phase 3.4.1** | `IMPLEMENTED_NOT_LIVE_VERIFIED` | `IMPLEMENTED_NOT_LIVE_VERIFIED` | `IMPLEMENTED_NOT_LIVE_VERIFIED` | `IMPLEMENTED_NOT_LIVE_VERIFIED` |

### What the "+13.5% Improvement" Actually Means:
- In pure LLM generation (Config A), models occasionally overlook edge cases (such as reverse proxy IP spoofing in CASE-01 or dual-write rollback in CASE-08).
- The dual-model + verifier pipeline (Config D) achieves a **modeled 13.5% uplift** because:
  1. The Critic explicitly searches for edge case omissions and passes findings back for revision (+8.9%).
  2. The deterministic verifier categorically prevents syntax, formatting, or invariant violations from passing unnoticed (+4.6%).
- **Sample Size Limitation**: A 10-task pilot is an illustrative qualitative benchmark, **not** a statistically conclusive dataset. Hundreds of trials across varied domains are needed for statistical significance.
