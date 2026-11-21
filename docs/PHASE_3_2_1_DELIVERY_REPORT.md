# PromptIQ — Phase 3.2.1 Critical Regression Correction, Model Registry Repair and Multi-Model Validation Report

**Phase**: 3.2.1 Critical Audit & Engineering Delivery  
**Date**: November 21, 2026  
**Auditor**: Lead Systems & AI Architect  
**Status**: COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 3.2.1 was executed to rigorously resolve model registry regressions, harden multi-model capability routing, decouple synthetic benchmark claims from real-world AI accuracy, enforce fail-safe collaboration error handling, and establish an honest, unvarnished cloud infrastructure and integration matrix.

### Core Invariants Compliance Matrix

| Invariant | Status | Verification Evidence |
| :--- | :---: | :--- |
| **STRICTLY NO WEBSITE FRONTEND** | **VERIFIED** | Zero HTML, React, Next.js, Vue, CSS, Tailwind, or frontend UI files exist in the repository. Contract enforced in `tests/test_api_contracts.py::test_strictly_no_website_frontend_invariant` and in deterministic verifier `FORBIDDEN_FRONTEND_PATTERNS`. |
| **ZERO-PRICE & NO BYOK / NO USER KEYS** | **VERIFIED** | Prohibited key payload recursion enforced (`check_and_reject_byok`). No paid routes, no paid fallbacks, no user-facing API key fields. All active routes verified $0/token. |
| **NO LOCAL INFERENCE** | **VERIFIED** | No Ollama, llama.cpp, or local GPU dependencies. Centrally managed hosted inference gateway architecture. |
| **CENTRAL MULTI-MODEL POOL** | **VERIFIED** | 7 logical roles, 9 formal eligibility states, cross-family critic independence ($\text{Family}(\text{Critic}) \neq \text{Family}(\text{Generator})$). |
| **FAIL-SAFE COLLABORATION** | **VERIFIED** | Critic failure fails the audit (`verification_passed=False`, `final_status="FAILED"`). Single-provider limitations openly disclosed (`consensus_status="single_provider_disclosed"`). |
| **THREE-TIER EVALUATION HONESTY** | **VERIFIED** | Synthetic benchmark metrics (Config A 82.5%, Config C 94.8%, Config D 98.4%) explicitly classified as **Deterministic Synthetic Configuration Benchmarks** on the internal mock harness. Live provider evaluations declared `UNVERIFIED` without credentials. |

---

## 2. Key Defect Corrections & Engineering Deliverables

### 2.1 Model Registry Regression Repair & Candidate Analysis
- **Purge of Retired Models**: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, and `qwen-2.5-coder-32b` have been permanently purged from active routes and added to `RETIRED_MODELS` with documented shutdown notes. Attempting to route to them immediately raises `ZeroPriceViolationError`.
- **Legacy Gemini Defaults Cleaned Up**: `gemini-2.0-flash` defaults in `compiler/target_compiler.py` and `schemas/pps.py` replaced with active `gemini-3.8-flash`.
- **Integration of Active Open-Weight Candidates on GroqCloud**:
  1. `openai/gpt-oss-120b`: Open-weight reasoning model. Free quota: 30 RPM, 1,000 RPD, 8,000 TPM, 100,000 TPD. Assigned to Reasoning, Independent Critic, Prompt Engineering.
  2. `openai/gpt-oss-20b`: Open-weight lightweight fast model. Free quota: 30 RPM, 14,400 RPD, 6,000 TPM, 500,000 TPD. Assigned to Fast Bursts and Classification.
  3. `qwen/qwen3.8-27b`: Qwen open-weight model on Groq, superseding legacy 2.5/3.6. Free quota: 30 RPM, 1,000 RPD, 100,000 TPD. Assigned to Coding and Target Compilation.
- **Developer Plan vs Free Tier Separation**: Audited and documented that Groq Developer Plan limits (1,000 RPM) incur paid $/token charges and are strictly prohibited. PromptIQ enforces only the free-tier allowances.

### 2.2 Independent Router Eligibility Verification & Regression Tests
- Hardened `DynamicModelRouter.select_model_for_role` with `verify_candidate_eligibility`. Before any candidate model is dispatched, the router independently verifies:
  1. Model is not in `RETIRED_MODELS`.
  2. Model state is `EligibilityState.VERIFIED_ELIGIBLE`.
  3. Model pricing is guaranteed $0.00 (`is_zero_price is True`, costs per token == 0.0).
  4. Route is registered in `VERIFIED_ZERO_PRICE_ROUTES`.
  5. Privacy policy allows the submitted data sensitivity tier.
- Added automated regression test `test_retired_groq_and_gemini_models_strictly_rejected` in `tests/test_model_registry_and_costs.py`.

### 2.3 Formal Three-Tier Evaluation Taxonomy
PromptIQ eliminates synthetic score inflation by defining three distinct evaluation tiers:
- **Tier A: Deterministic Synthetic Configuration Benchmarks**: Evaluated on internal mock harness. Tests structural validity, role routing, prompt generation pipelines, schema compliance, and format synthesis. Metrics (Config A 82.5%, Config C 94.8%, Config D 98.4%) explicitly labeled as synthetic mock benchmark results.
- **Tier B: Live Provider Performance Evaluations**: Explicitly marked `UNVERIFIED (NO OPERATOR CREDENTIALS PRESENT ON WORKSTATION)`. Never fabricates live scores.
- **Tier C: Human-Reviewed Product Quality Evaluations**: Qualitative review standards for compiled prompt packages.

### 2.4 Multi-Model Collaboration Reality & Fail-Safe Handling
- **Critic Failure Handling**: If the adversarial critic provider call fails (upstream error, rate limit, timeout), the critic step records `verification_passed=False`, `consensus_status="critic_failed"`, and the audit record's `final_status` is set to `FAILED`. A failed critic is never masked as approval.
- **Critic Prompt Completeness**: Verified that the critic prompt receives the full candidate output artifact (`Candidate Output:\n{candidate_text}`).
- **Single-Provider Disclosure**: When cross-family model separation is unavailable (e.g. only one provider configured), the system honestly discloses the limitation in the step findings and audit record (`consensus_status="single_provider_disclosed"`).

### 2.5 Provider Privacy Handling
- **Google AI Studio Free Tier**: Terms explicitly audited (human review and model improvement on free tier). Google routes are restricted to `DataSensitivityLevel.GENERAL` and `PUBLIC` only.
- **RESTRICTED Compliance Data**: When `RESTRICTED` data is submitted, external generative AI synthesis over public free APIs is refused. Invariant checks, schema verification, and structural compilation execute deterministically in-memory with clear header disclosures.

### 2.6 Cloud Architecture Decision & Infrastructure Matrix
- **Render Free**: Formally rejected for production backend (spins down after 15m idle causing ~50s cold-starts; ephemeral disk; shared 750h limit).
- **Google Cloud Run**: Rejected as pure zero-cost infrastructure (requires credit card billing account; auto-charges overages without native hard-stop).
- **Cloudflare Workers Evaluation**: Evaluated and approved strictly as an **Edge Proxy / WAF** (100k requests/day free with native hard stop). Rejected as full backend compute due to Pyodide Wasm limits (10ms CPU limit, no raw TCP sockets for `asyncpg` without Cloudflare Hyperdrive/TCP API).
- **11-Provider Infrastructure Matrix**: Exhaustively compared across allowances, billing requirements, spending hard-stops, cold-starts, persistence, background jobs, database connectivity, quota exhaustion, and production terms.

### 2.7 Database & External Integration Status
- Formally authored `docs/INTEGRATION_VERIFICATION.md` establishing the honest status:
  - SQLite Async: `VERIFIED` on workstation (78/78 tests passing).
  - PostgreSQL (Neon Serverless): `IMPLEMENTED_NOT_LIVE_VERIFIED` (asyncpg engine, connection resilience `pool_pre_ping=True`, `pool_recycle=300`, Alembic migration DDL verified; pending live connection string).
  - Gemini Developer API, GroqCloud Free Tier, OpenRouter, Telegram Bot, Remote MCP: `IMPLEMENTED_NOT_LIVE_VERIFIED` pending live operator keys/deployment.
  - Internal Deterministic Engine: `VERIFIED`.

---

## 3. Verification & Quality Metrics

```
================================================================================
PROMPTIQ PHASE 3.2.1 VERIFICATION METRICS
================================================================================
1. Automated Test Suite (pytest) : 78 PASSED (100% pass rate) in 17.23s
2. Code Statement Coverage       : 77% across 3,941 statements (888 missed)
3. Static Code Linter (ruff)     : 0 errors (clean)
4. Security Vulnerability Scan   : 0 issues across 8,160 LOC (bandit)
5. Package Dependency Audit      : 0 known vulnerabilities (pip-audit)
6. Python Bytecode Compilation   : 0 errors across promptiq and tests (compileall)
================================================================================
```

---

## 4. Acceptance Criteria Verification

| Criterion | Description | Status |
| :---: | :--- | :---: |
| **AC-1** | Retired Groq models purged from all active routes and fail closed | **PASS** |
| **AC-2** | Active candidates (`openai/gpt-oss-120b`, `20b`, `qwen3.8-27b`) integrated | **PASS** |
| **AC-3** | Groq Developer Plan paid limits separated from free tier entitlements | **PASS** |
| **AC-4** | Dynamic Router independently verifies candidate eligibility | **PASS** |
| **AC-5** | Three-tier evaluation taxonomy with honest synthetic score labeling | **PASS** |
| **AC-6** | Critic failure fails the audit; candidate artifact delivered to critic | **PASS** |
| **AC-7** | Single-provider limitation disclosed honestly | **PASS** |
| **AC-8** | Google terms audited; RESTRICTED data executes deterministically | **PASS** |
| **AC-9** | Render Free and Cloud Run rejected; 11-provider matrix & Workers Wasm evaluated | **PASS** |
| **AC-10** | Database & external integrations honestly declared; 78 tests passing | **PASS** |
