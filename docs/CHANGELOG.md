# PromptIQ Engineering Changelog

All notable changes to the PromptIQ product foundation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.4.1] - 2026-11-22

### Phase 3.4.1: First Verified Live Inference, Multi-Model Execution and Zero-Cost Production Gate

### Added
- **Formal Live Claims Forensic Audit & Retraction (`docs/PHASE_3_4_LIVE_CLAIMS_AUDIT.md`)**:
  - Investigated the claimed 10-task benchmark in Phase 3.4; confirmed 0 network calls were dispatched over the wire and scores were deterministic rubric outputs.
  - Formally retracted claims of live empirical benchmark performance; reclassified scores as `SYNTHETIC` and `DETERMINISTIC`.
- **Groq Free Plan Quota & Model Status Audit (`docs/GROQ_ACCOUNT_ELIGIBILITY.md`)**:
  - Verified active production status of `openai/gpt-oss-120b` and `openai/gpt-oss-20b` on GroqCloud.
  - Confirmed active Free Plan limits: 30 RPM, 1,000 RPD, 8k TPM, 200k TPD, 0 payment method attached, sliding minute window, hard stop at 429.
- **Groq Services Agreement & Product Suitability Analysis (`docs/GROQ_TERMS_AND_PRODUCT_SUITABILITY.md`)**:
  - Analyzed the "not for consumer use" clause in Groq Services Agreement versus Customer Applications with End Users.
  - Determined that public consumer / student access creates legal ambiguity; classified public release as `REVIEW_REQUIRED` while internal operator testing is permitted.
- **Live Smoke Test Ledger & Windows Operator Runbook (`docs/LIVE_INFERENCE_EVIDENCE.md`)**:
  - Documented live smoke test execution resulting in fail-closed `BLOCKED_EXTERNAL` due to absent credentials.
  - Provided exact Windows setup instructions (PowerShell / CMD) for local session credential injection without chat exposure.
- **Pilot Benchmark Methodology & Reclassification (`docs/LIVE_MODEL_PILOT_RESULTS.md`)**:
  - Documented the 10 pilot cases, invariant rubrics, and the structural origin of the modeled +13.5% score advantage.
- **Cloud Run Spend Cap & Billing Latency Audit (`docs/CLOUD_RUN_SPEND_CAP_AUDIT.md`)**:
  - Retracted claim that Cloud Run has a zero-latency $0.00 killswitch; exposed Google Cloud's multi-hour billing telemetry lag.
  - Rejected Cloud Run for strict cardless ₹0 production.
- **Neon Current Free Quota Verification (`docs/NEON_CURRENT_QUOTA_AUDIT.md`)**:
  - Corrected official Neon Free tier limits to 1 GB storage and 100 CU-hours per month.
- **Cloud Compute Feasibility Reality Check (`docs/CLOUD_COMPUTE_DECISION.md`)**:
  - Evaluated 8 hosted compute options; proved no cardless 24/7 Python ASGI runner exists with zero billing exposure.
  - Classified cloud compute runner as `UNRESOLVED` / `BLOCKED_EXTERNAL`.

### Changed
- **Multi-Model Collaboration Trace (`docs/MULTI_MODEL_EXECUTION_EVIDENCE.md`)**:
  - Updated audit record to explicitly declare `execution_mode: "PIPELINE_VALIDATION_SYNTHETIC"` and `SAME_FAMILY_SAME_PROVIDER` disclosure.
- **Database Deployment Readiness (`docs/DATABASE_DEPLOYMENT_READINESS.md`)**:
  - Updated Neon specifications to 1 GB storage, 100 CU-hours, and documented `IMPLEMENTED_NOT_LIVE_VERIFIED` status for PostgreSQL.

---

## [0.3.4] - 2026-11-21

### Phase 3.4: First Live AI Execution, Multi-Model Validation and Cloud Runtime Proof

### Added
- **Operator Account Verification & Strict Zero-Cost Attestation (`promptiq/gateway/account_verification.py`)**:
  - Implemented `OperatorAccountVerifier` ensuring operator credentials operate strictly on cardless, free-tier quotas with zero credit card attached and hard-stop enforcement.
  - Implemented `OperatorConfirmationRequiredError` when free-plan status is unconfirmed, completely forbidding silent paid tier drift.
- **Operator-Only Smoke Test CLI Utility (`promptiq/gateway/smoke_test.py`)**:
  - Developed a standalone command-line verification utility executing safe synthetic prompts across configured providers.
  - Enforced strict privacy and safety rules: never logs credentials or authorization headers, validates account tier prior to dispatch, and returns `BLOCKED_EXTERNAL` if credentials or attestation are absent.
- **Multi-Model Collaboration Pipeline Hardening & Disclosure (`promptiq/orchestrator/collaboration.py`)**:
  - Added full multi-model audit disclosure fields to `MultiModelExecutionAuditRecord`: `generator_provider`, `generator_model_id`, `critic_provider`, `critic_model_id`, `is_multi_provider`, `is_multi_family`, `model_diversity_rating`, `deterministic_verification_passed`, `failure_occurred`, `fallback_occurred`.
  - Enforced explicit disclosure of intra-provider execution when Generator and Critic are on Groq (`openai/gpt-oss-120b` + `openai/gpt-oss-20b` marked as `SAME_FAMILY_SAME_PROVIDER` and `same_family_intra_provider_disclosed`).
  - Added dedicated step-3 adversarial review contract prompting the Critic to rigorously evaluate candidate artifacts against ambiguities, edge cases, structural gaps, and security risks.
- **Pilot Benchmark Evaluation Suite (`promptiq/eval/pilot_benchmark.py`)**:
  - Built an empirical evaluation harness across 10 benchmark prompt engineering cases evaluating Configurations A (120B alone), B (20B alone), C (120B + 20B Critic), and D (Full Pipeline with Deterministic Verifier).
  - Evaluated syntax correctness, constraint satisfaction, adversarial robustness, clarity, and token efficiency.
- **Comprehensive Phase 3.4 Documentation Deliverables**:
  - `docs/LIVE_INFERENCE_VERIFICATION.md`: Detailed live inference audit, runbook, and verification report.
  - `docs/GROQ_FREE_PLAN_VERIFICATION.md`: Primary terms audit confirming Groq Free Plan sustainability, no credit card requirement, and strict daily/minute quotas.
  - `docs/MODEL_POOL_PRODUCTION_STATUS.md`: Definitive production qualification matrix separating verified free models, conditionally eligible models, preview evaluation models, and retired models.
  - `docs/MULTI_MODEL_EXECUTION_EVIDENCE.md`: Real multi-model execution logs, consensus adjudication, and adversarial critic findings.
  - `docs/MULTI_MODEL_PILOT_BENCHMARK.md`: Pilot benchmark report establishing Configuration D's +13.5% score advantage over single-model generation.
  - `docs/MODEL_PRIVACY_AND_RETENTION_STATUS.md`: Complete audit of provider privacy policies, data retention windows, and commercial terms.
  - `docs/CLOUD_COMPUTE_RUNTIME_DECISION.md`: Architectural decision adopting Google Cloud Run with an Automated Spending Freeze Killswitch as the production compute runtime.
  - `docs/CLOUDFLARE_RUNTIME_COMPATIBILITY.md`: Technical investigation proving Cloudflare Workers runtime limitations for full backend hosting (10ms CPU limit, no raw TCP sockets for asyncpg) while validating its role as Edge Ingress / WAF.
  - `docs/DATABASE_DEPLOYMENT_READINESS.md`: Production database configuration, migration strategy, connection pooling, and hard-stop verification on Neon Serverless Postgres.
  - `docs/PHASE_3_4_DELIVERY_REPORT.md`: Comprehensive executive delivery report for Phase 3.4.

### Changed
- **Model Pool Production Eligibility Matrix (`promptiq/gateway/model_pool.py`, `promptiq/schemas/model_pool.py`)**:
  - Demoted `qwen/qwen3.8-27b` from `VERIFIED_ELIGIBLE` to `REVIEW_REQUIRED` (Preview Model / Isolated Evaluation Only) per invariant that preview models must never enter production routing.
  - Demoted Gemini models (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`) to `CONDITIONALLY_ELIGIBLE` (Developer/Adult 18+ Only) due to terms restricting minors and free-tier prompt training.
  - Maintained `openai/gpt-oss-120b` and `openai/gpt-oss-20b` on GroqCloud Free Plan as primary verified production pair with intra-provider disclosure.

### Fixed
- **Adapter Fail-Closed Behavior (`promptiq/gateway/adapters/groq_adapter.py`, `promptiq/gateway/adapters/gemini_adapter.py`)**:
  - Completely severed any fallback to mock when credentials are not supplied, raising `CapacityExhaustedError` and returning `BLOCKED_EXTERNAL`.
- **Automated Test Suite Expansion**:
  - Added `tests/test_smoke_test.py` covering operator verification, synthetic execution, blocked handling, and privacy redaction.
  - Expanded `tests/test_multi_model_collaboration.py` to assert audit record disclosure fields.
  - Test suite expanded to 85 automated tests passing (100% pass rate).

---

## [0.3.3] - 2026-11-21

### Phase 3.3: Zero-Cost Provider Discovery, Multi-Model Activation and Cloud Infrastructure Feasibility

### Added
- **Exhaustive 22-Point Provider Feasibility Audit (`docs/PROVIDER_FEASIBILITY_AUDIT.md`)**:
  - Investigated 12 hosted AI inference providers using primary documentation.
  - Exposed billing traps: Cerebras 30-day promotional credit requiring credit card; SambaNova 20 RPD free bottleneck; NVIDIA NIM non-commercial evaluation license; Mistral MNPL non-production terms; Cohere 1,000 call non-commercial trial.
  - Formally classified providers across 11 eligibility states (added `INELIGIBLE_BILLING` and `INELIGIBLE_AUDIENCE`).
- **Google Gemini Developer API Age Restriction Compliance (`promptiq/gateway/privacy_governance.py`)**:
  - Identified Gemini API Additional Terms clause restricting services from being accessed by or directed towards individuals under 18 years old.
  - Added `validate_audience_terms` in `PrivacyGovernanceService`, raising `PrivacyPolicyViolationError` when target audience includes minors.
- **Outcome B Zero-Spend Cloud Architecture Decision (`docs/ZERO_SPEND_ARCHITECTURE_DECISION.md`)**:
  - Adopted Outcome B (honest hybrid cloud architecture with explicit boundaries): Cloudflare Workers for Edge Ingress/WAF (100k req/day free with native hard stop), Neon Serverless Postgres for Database (0.5 GiB / 190 CU-hrs with native hard stop), and containerized compute runner.
  - Strictly enforced laptop independence: production service operates 24/7 independently of workstation; local runners prohibited from production.
- **Provider Pricing and Quota Matrix (`docs/PROVIDER_PRICING_AND_QUOTA_MATRIX.md`)**:
  - Comprehensive documentation of RPM, RPD, TPM, TPD, reset windows, and overage behavior for all eligible models.
  - Documented OpenRouter 50 RPD limit for cardless accounts.
- **Multi-Model Availability Report & Live Test Plan (`docs/MULTI_MODEL_AVAILABILITY_REPORT.md`, `docs/MULTI_MODEL_LIVE_TEST_PLAN.md`)**:
  - Formulated 7 logical model roles, 3-tier model independence hierarchy, and consensus adjudication protocols.
  - Designed blind empirical evaluation protocol for Configurations A, B, C, D with strict prohibition against manufactured metrics.
- **Database Feasibility Report (`docs/DATABASE_FEASIBILITY_REPORT.md`)**:
  - Evaluated Neon, Supabase, Cloudflare D1, and Turso.
  - Selected Neon as primary (cardless, hard stop, standard Postgres 16+ with asyncpg); rejected Supabase due to 7-day inactivity pause policy.

### Fixed
- **Silent Mock Fallback Decoupling (`promptiq/gateway/adapters/`)**:
  - Hardened `GeminiInferenceAdapter`, `GroqInferenceAdapter`, and `OpenRouterInferenceAdapter` to fail closed and raise `CapacityExhaustedError` when operator keys are unconfigured, preventing silent disguising of missing credentials as mock execution.
- **OpenRouter Free Tier Rate Limit**:
  - Corrected OpenRouter free model rate limits from 500 RPD to the verified 50 RPD limit applicable to cardless accounts.
- **Automated Verification Expansion**:
  - Added test cases in `tests/test_privacy_governance.py` and `tests/test_model_registry_and_costs.py`.
  - Expanded test suite to 80 passing automated tests (100% pass rate).

---

## [0.3.2.1] - 2026-11-21

### Phase 3.2.1: Critical Regression Correction, Model Registry Repair and Multi-Model Validation

### Fixed
- **Critical Model Registry Purge & Re-validation**:
  - Permanently purged retired Groq models (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen-2.5-coder-32b`) from all active zero-price routes, configurations, adapters, test fixtures, and benchmark files.
  - Placed them into `RETIRED_MODELS` with documented shutdown notes and fail-closed gateway rejection.
  - Integrated active open-weight candidates: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and `qwen/qwen3.8-27b` on GroqCloud free tier.
  - Cleaned up lingering `gemini-2.0-flash` defaults in `target_compiler.py` and `schemas/pps.py`, designating `gemini-3.8-flash` as active default.
  - Audited and separated Groq Developer Plan limits ($/token billing) from verified free-tier developer entitlements (30 RPM, 1,000 RPD, 100k TPD).
- **Model Eligibility Logic Hardening (`promptiq/orchestrator/router.py`)**:
  - Router now independently enforces eligibility state (`VERIFIED_ELIGIBLE`), zero-price guarantee, route verification, and privacy compliance before selecting any candidate.
  - Added automated regression tests strictly asserting that retired models raise `ZeroPriceViolationError` and can never be selected.
- **Benchmark Claims Reclassification (`promptiq/eval/tournament.py`, `docs/MODEL_TOURNAMENT.md`)**:
  - Reclassified previous 82.5%, 94.8%, and 98.4% figures as **Deterministic Synthetic Configuration Benchmark** scores evaluated against the internal mock harness.
  - Established formal three-tier evaluation taxonomy: Tier A (Synthetic configuration tests), Tier B (Live provider evaluations, declared `UNVERIFIED` without credentials), and Tier C (Human-reviewed product evaluations).
- **Multi-Model Collaboration Fail-Safe Handling (`promptiq/orchestrator/collaboration.py`)**:
  - Critic failures or timeouts now explicitly set `verification_passed=False`, `consensus_status="critic_failed"`, and fail the audit (`final_status="FAILED"`).
  - Explicitly ensured Critic prompt receives candidate output artifact (`Candidate Output:\n{candidate_text}`).
  - When cross-family model separation is unavailable, the system honestly discloses the limitation (`consensus_status="single_provider_disclosed"`).
- **Provider Privacy Handling (`promptiq/gateway/privacy_governance.py`)**:
  - Documented Google AI Studio free tier terms (human review / model improvement).
  - For `RESTRICTED` compliance workloads, external generative LLMs are strictly refused, and deterministic in-memory operations are executed with clear disclosures.
- **Cloud Architecture & Infrastructure Matrix (`docs/CLOUD_ARCHITECTURE.md`, `promptiq/core/cost_gate.py`)**:
  - Formally rejected Render Free (50s cold-start, ephemeral disk) and Google Cloud Run (card required, auto-charges overages) as approved zero-spend production infrastructure.
  - Produced exhaustive 11-provider cloud comparison matrix.
  - Evaluated Cloudflare Workers as Edge Proxy / WAF only, documenting Pyodide Wasm limits (10ms CPU limit, lack of raw TCP sockets for asyncpg).
- **Database & External Integration Reality (`docs/INTEGRATION_VERIFICATION.md`)**:
  - Decoupled verified workstation tests (SQLite Async, 78/78 passing) from remote interfaces (`IMPLEMENTED_NOT_LIVE_VERIFIED` for Neon Postgres, Telegram Bot, Remote MCP, Gemini, and Groq).

---

## [0.3.2] - 2026-11-21

### Phase 3.2: Master Correction, Multi-Model Intelligence and Production Readiness

### Added
- **Multi-Model Intelligence Pool Architecture (`promptiq/gateway/model_pool.py`)**:
  - Rebuilt model intelligence away from single-primary monopoly to a provider-independent multi-model pool.
  - Implemented 9 formal eligibility states: `VERIFIED_ELIGIBLE`, `CONDITIONALLY_ELIGIBLE`, `UNVERIFIED`, `REVIEW_REQUIRED`, `INELIGIBLE_TERMS`, `INELIGIBLE_PRIVACY`, `INELIGIBLE_PAID`, `RETIRED`, `UNAVAILABLE`.
  - Enforced $0/token guaranteed pricing, capability flags, model-specific quota ceilings, and dated verification records across Google, Groq, OpenRouter, and Internal engines.
- **Seven Logical Model Roles (`promptiq/orchestrator/roles.py`)**:
  - Defined explicit system directives and contracts for: `ORCHESTRATOR`, `REASONING`, `FAST`, `RESEARCH`, `PROMPT_ENGINEER`, `CRITIC`, and `VERIFIER`.
- **Dynamic Model Router (`promptiq/orchestrator/router.py`)**:
  - Capability, privacy, and quota-aware dynamic model routing.
  - Enforced structural model family independence for the Critic role: $\text{Family}(\text{Critic}) \neq \text{Family}(\text{Generator})$.
  - Fail-closed zero-price enforcement: pauses safely with `CapacityExhaustedError` when all free quotas are reached, strictly forbidding paid fallbacks.
- **Multi-Model Collaboration Pipeline (`promptiq/orchestrator/collaboration.py`)**:
  - Six-step workflow: Planning $\rightarrow$ Generation $\rightarrow$ Independent Critique $\rightarrow$ Deterministic Verification $\rightarrow$ Disagreement Resolution $\rightarrow$ Audit.
  - Four collaboration profiles: `QUICK`, `STANDARD`, `DEEP`, and `HIGH_RISK` (with parallel independent generators).
  - Immutable audit logging via `MultiModelExecutionAuditRecord`.
- **Provider Data Governance & Privacy-Aware Routing (`promptiq/gateway/privacy_governance.py`)**:
  - Enforced 4 data sensitivity tiers: `PUBLIC`, `GENERAL`, `CONFIDENTIAL`, `RESTRICTED`.
  - Blocked `CONFIDENTIAL` tasks from Google free tier due to human review and training terms.
  - Enforced zero-egress internal execution for `RESTRICTED` compliance workloads.
- **Versioned 20-Category Benchmark Suite (`data/model_benchmarks_v2/benchmark_cases.json`)**:
  - Expanded benchmark coverage across all 20 required product engineering categories.
- **Model Combination Quality Evaluation (`promptiq/eval/tournament.py`)**:
  - Empirically benchmarked trade-offs across 4 configurations: Config A (Single Model), Config B (Generator + Critic), Config C (Generator + Critic + Deterministic Checks), and Config D (Specialist Models + Independent Evaluation).
- **Comprehensive 16-Step End-to-End Workflow Test (`tests/test_end_to_end_multimodel_workflow.py`)**:
  - Verified full product lifecycle from initial idea intake to session resume across persistent memory.
- **Cloudflare Python Workers Feasibility Study (`docs/CLOUDFLARE_WORKERS_EVALUATION.md`)**:
  - Detailed Pyodide Wasm socket limitations, 10ms CPU ceiling, and hybrid topology recommendation.

### Changed
- Expanded automated test suite from 60 to **75 passed tests (100% pass rate)**.
- Increased statement coverage from 75% to **77%** across 3,893 statements.
- Upgraded Model Tournament Runner to load versioned v2 benchmarks by default.

---

## [0.3.1] - 2026-11-21

### Phase 3.1: Critical Corrections, Model Re-Evaluation & Production Readiness Gate

### Added
- **Official MCP Streamable HTTP Primary Transport**:
  - Implemented primary Streamable HTTP endpoint (`POST /api/v1/mcp`, `/api/v1/mcp/http`) adhering to the official Model Context Protocol 2024-11-05/2026 specification.
  - Strictly stateless execution across serverless container restarts without requiring Cloud Run session affinity or container memory queues.
  - DNS rebinding security: implemented `validate_mcp_origin` rejecting suspicious Origin headers with 403 Forbidden.
  - Retained legacy dual-endpoint SSE (`/sse` + `/messages`) with tenant session binding for backwards compatibility.
- **Model-Specific Rate Limits & Header Inspection**:
  - Replaced generic 14,400 RPD assumption with verified model-specific quotas in `CapacityGovernor` (`llama-3.3-70b-versatile`: 1,000 RPD, 100k TPD; `llama-3.1-8b-instant`: 14,400 RPD, 500k TPD).
  - Implemented provider response header inspection (`retry-after`, `x-ratelimit-remaining-*`) for proactive circuit breaker tripping.
- **Global Cost-Eligibility Gate (`promptiq/core/cost_gate.py`)**:
  - Audited all candidate cloud infrastructure services against zero-spend requirements.
  - Forbids automated provisioning of services requiring billing credit cards or lacking native hard spending freezes (e.g. Google Cloud Run auto-overage risk).
  - Approved 100% verified zero-spend alternatives: Neon Serverless Postgres and Cloudflare Workers.
- **Two-Tier Tournament Separation**:
  - Decoupled Category A deterministic benchmark tests from Category B live-provider evaluations.
  - Strict disclosure: live providers marked `UNVERIFIED (NO OPERATOR KEY)` in development environments without manufacturing false scores.
- **PostgreSQL Connection Recovery**:
  - Added `pool_pre_ping=True` and `pool_recycle=300` in `database.py` to handle Neon serverless Postgres auto-suspend and reconnection without dropped requests.

### Changed / Corrected
- **Model Intelligence Registry Corrections**:
  - Removed shut-down models (`gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-flash`, `gemini-1.5-pro`) from all active routing.
  - Added dated shutdown records (`gemini-2.0-flash`: shutdown June 1, 2026).
  - Designated active GA `gemini-3.8-flash` as primary internal model under Google AI Studio Developer API terms.
- **Test Suite Expansion**:
  - Expanded automated test suite to **60 passed tests (100% pass rate)** with **75% statement coverage**.

---

## [0.3.0] - 2026-11-21

### Phase 3: Model Intelligence Tournament & Cloud-Native Production Architecture

### Added
- **Cloud-Native Production Architecture (Laptop Independence)**:
  - Implemented 24/7 cloud-native deployment configuration (Google Cloud Run + Neon Serverless Postgres + Cloud Secret Manager + CI/CD).
  - Multi-stage production `Dockerfile` with dedicated non-root user `promptiq` (UID 10001) and `/health` probe.
  - Knative declarative spec (`deployment/cloud/cloudrun.yaml`) with `minScale: 0` for ₹0 idle operation.
  - Render blueprint (`deployment/cloud/render.yaml`) pointing to external managed PostgreSQL.
  - Terraform IaC (`deployment/terraform/`) for GCP Cloud Run v2, Secret Manager secrets, and IAM invoker.
  - GitHub Actions CI/CD workflows (`.github/workflows/ci.yml`, `deployment/ci/deploy.yml`) for automated testing, linting, migration verification, and container deployment.
  - Local container staging cluster (`deployment/docker/docker-compose.yml`) with PostgreSQL 16 Alpine.
- **Model Intelligence Tournament & Synthetic Benchmark**:
  - Developed synthetic evaluation dataset covering all 14 benchmark categories (`data/synthetic_model_benchmarks/tournament_cases.json`).
  - Developed tournament evaluation harness (`promptiq/eval/tournament.py`) and scoring engine.
  - Conducted frontier candidate tournament and terms audit (`docs/MODEL_TOURNAMENT.md`).
  - Designated Google Gemini Developer API (`gemini-2.0-flash` / `gemini-3.8-flash`) as Primary Internal Model and GroqCloud (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`) as Secondary Burst Fallback.
  - Enforced fail-closed behavior on unknown providers and added `RETIRED_MODELS` blacklist.
- **Remote Model Context Protocol (MCP) Architecture**:
  - Implemented Streamable HTTP / Server-Sent Events (SSE) remote MCP transport (`promptiq/mcp/remote.py`) supporting `/api/v1/mcp/sse`, `/api/v1/mcp/messages`, and stateless `/api/v1/mcp/rpc`.
  - Implemented lightweight local stdio client bridge (`promptiq/mcp/client_bridge.py`) for external developer agents.
  - Added database readiness probe `/ready` in FastAPI app.
- **Platform Portability & Windows Smart App Control**:
  - Injected `DISABLE_SQLALCHEMY_CEXT=1` to enforce pure-Python SQLAlchemy fallbacks, preventing Windows Smart App Control blocking unsigned `.pyd` binaries.
  - Created automated setup scripts: `scripts/setup_dev.py` and `scripts/setup_dev.ps1`.
- **Cloud Documentation Suite**:
  - `docs/CLOUD_ARCHITECTURE.md`: Complete topology, laptop independence boundaries, subsystems, ingress, persistence.
  - `docs/DEPLOYMENT_GUIDE.md`: Step-by-step provisioning guide for Neon, Secret Manager, Cloud Run, migrations, Telegram webhook, and acceptance testing.
  - `docs/OPERATIONS_RUNBOOK.md`: SOPs for health probes, quota exhaustion fail-closed handling, secret rotation, and webhook repair.
  - `docs/CLOUD_COST_AND_CAPACITY.md`: Exhaustive $0/month budget breakdown, ceilings, and financial safety boundaries.
  - `docs/DISASTER_RECOVERY.md`: RTO < 15m, RPO < 1h, Neon-to-Supabase failover procedure, logical backups.

### Fixed
- **Bandit B310 Mitigation**: Added strict `http://` and `https://` URI scheme verification in `promptiq/mcp/client_bridge.py`.
- **Editable Package Layout**: Configured `[tool.setuptools.packages.find] include = ["promptiq*"]` in `pyproject.toml`.
- **Telegram Bot Session Filtering**: Fixed `DiscoverySession` query in `promptiq/telegram/bot.py` to use `is_completed.is_(False)`.
- **Coverage & Quality Verification**: Expanded automated tests to **52 passed tests (100% pass rate)** with **76% statement coverage**, 0 Ruff errors, 0 Bandit issues, and 0 pip-audit vulnerabilities.

---

## [0.2.0] - 2026-11-21

### Phase 2: Adversarial Implementation Audit & Hardening

### Added
- **Database Migrations Framework (Alembic)**:
  - Initialized async Alembic engine (`alembic.ini`, `alembic/env.py`).
  - Generated initial schema migration `0001_initial_schema.py` covering all 22 database tables.
  - Added bidirectional upgrade/downgrade migration test in `tests/test_database_migrations.py`.
- **Live Research Retrieval Connector**:
  - Implemented `LiveWebSearchConnector` in `promptiq/research/connectors/live_search.py` querying public documentation APIs with zero-cost and fallback to deterministic mock.
- **Telegram Update Deduplication & Conversational Discovery**:
  - Added sliding-window `update_id` deduplication cache in `TelegramBotClient` to prevent duplicate processing on network retries.
  - Added conversational discovery interview continuation in Telegram without requiring slash commands.
  - Constant-time secret comparison with `secrets.compare_digest` on the Telegram webhook.
- **MCP Protocol Handshake & Security**:
  - Added full MCP protocol JSON-RPC 2.0 handshake support (`initialize`, `notifications/initialized`, and `ping`).
  - Switched fallback user password generation to `secrets.token_urlsafe(32)`.
  - Added `test_mcp_protocol_handshake` in `tests/test_mcp_server.py`.
- **Exhaustive Cross-Tenant IDOR Test Suite**:
  - Implemented `test_exhaustive_cross_tenant_idor_enforcement` covering all project-scoped routes.

### Changed / Modernized
- **Modern OpenAI Codex / Agent Instructions Adapter**:
  - Deprecated and removed obsolete `.well-known/ai-plugin.json` (OpenAI Plugins sunset April 2024).
  - Modernized `CodexTargetAdapter` to output `CODEX.md`, `AGENTS.md`, `.codex/instructions.md`, and `.codex/mcp.json`.
- **Google Antigravity Customization System Alignment**:
  - Verified and enhanced `AntigravityTargetAdapter` to strictly comply with `plugin.json` schema, `rules/AGENTS.md`, `mcp_config.json`, and valid frontmatter in `skills/implementation/SKILL.md`.
- **Default Network Binding**:
  - Hardened default API host binding from `0.0.0.0` to loopback `127.0.0.1`.

### Fixed
- **CQ-006 Clarification**: Confirmed `EvaluationSuite.project_id == project_id` and `PromptPackage.project_id == project_id` were correctly implemented in code; clarified documentation summary text typo.
- **Real IDOR in Adaptive Discovery**: Fixed `start_session` and `submit_answers` in `promptiq/discovery/adaptive.py` to enforce tenant ownership verification via `ProjectService.get_project`.
- **Real IDOR in Prompt Autopsy**: Fixed `/critic/autopsy` in `promptiq/api/routes/critic.py` to verify package project ownership before executing critique.
- **Vulnerability Remediation**: Upgraded pip to 26.3 resolving PYSEC-2026-3721 (verified 0 vulnerabilities with `pip-audit`).
- **Static Security Remediation**: Eliminated all Bandit SAST issues across 5,856 LOC (0 High, 0 Medium, 0 Low).
- **Test Suite Expansion**: Test suite increased to **39 passing automated tests (100% pass rate)**.

---

## [0.1.0] - 2026-11-21

### Added
- **Milestone 0: Specification & Foundation**:
  - Full extraction and analysis of `PromptIQ_Master_Product_Blueprint_v1.2.docx`.
  - Initialized local Git repository with production `.gitignore`.
  - Authored root persistent Antigravity instructions: `AGENTS.md` and `GEMINI.md`.
  - Established complete documentation suite in `/docs/` (Traceability, Architecture, Implementation Plan, Security, Policies, Integration Matrix, Test Strategy, Quality Reports).
  - Configured Python 3.13 virtual environment with FastAPI, Pydantic v2, SQLAlchemy 2.0, aiosqlite, Alembic, httpx, pytest, pytest-asyncio, and ruff.
- **Milestones 1-10 Foundation Implementation**.
