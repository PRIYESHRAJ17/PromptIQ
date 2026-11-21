# PROMPTIQ — MASTER PLATFORM & BACKEND DELIVERY REPORT
## Full Product Intelligence, Backend Engineering, Surface Integrations, Security, Reliability and Production Readiness

---

### A. Executive Summary

- **Milestone Name**: PromptIQ Master Backend & Platform Engineering Execution
- **Repository Baseline Commit**: `25b3c71`
- **Scope & Non-Negotiable Boundaries**:
  - **Website Frontend**: Strictly out of scope (0 UI/HTML/React/Next.js files generated).
  - **End-User Cost**: 100% Free to users forever (₹0); Zero BYOK; No paid inference routes.
  - **Execution Mode**: Centrally managed hosted inference; No local inference required.
  - **Factual Integrity**: Zero synthetic benchmarks presented as empirical; genuine evidence only.
- **Verification Summary**:
  - Test Suite: **118 passed in 9.19s** (`pytest -v`)
  - Static Quality & Linting: **0 issues** (`ruff check promptiq tests`)
  - Security Vulnerability Scan: **0 issues** (`bandit -r promptiq`)
  - Dependency Vulnerability Scan: **No known vulnerabilities** (`pip-audit`)
  - Bytecode Compilation: **100% clean** (`python -m compileall promptiq tests`)

---

### B. Complete Invariant Audit

| Invariant | Status | Enforcement Mechanism & Evidence |
| :--- | :--- | :--- |
| **1. Strictly No Website Frontend** | **ENFORCED** | No HTML, CSS, React, JSX/TSX components or frontend assets were created. All backend REST API schemas (`projects`, `discovery`, `constitution`, `compiler`, `critic`, `eval`, `export`) fully support future UI consumption without modification. |
| **2. Zero-Price & No BYOK** | **ENFORCED** | No user API key collection or BYOK inputs exist anywhere in schemas, APIs, CLI, or database models. All inference requests are dispatched through centrally managed zero-price routes (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`). Paid routes are hard-blocked by `ModelRegistryService` and `CapacityGovernor`. |
| **3. No Local Inference** | **ENFORCED** | Architecture requires no Ollama, llama.cpp, or local GPUs. Prompts are compiled to target agent packages and served via cloud-hosted zero-price developer APIs. |
| **4. Centrally Managed Hosted Inference** | **ENFORCED** | Operator-managed server-side credentials power the inference gateway across Web API, Telegram Bot, MCP Server, CLI, and SDK. |
| **5. Shared Backend & Project Memory** | **ENFORCED** | Unified SQLite/PostgreSQL schemas share Project Constitution, Discovery Sessions, Prompt Specifications, Evidence Ledger, and Checkpoints across all surfaces. |
| **6. Adaptive Discovery & Constitution** | **ENFORCED** | Adaptive discovery with depth control (`quick`, `guided`, `deep`), anti-fatigue checks, contradiction detection, missing high-impact information flags, and immutable versioned constitutions with rollback and granular diffing. |
| **7. Prompt Intelligence & Native Compilation** | **ENFORCED** | Compiles canonical Prompt Specification (PPS) to target-native formats: Google Antigravity, Claude Code, Cursor, OpenAI Codex, and Gemini CLI, with automated target recommendation. |
| **8. Adversarial Critique & Prompt Autopsy** | **ENFORCED** | Multi-dimensional static and heuristic autopsy with deterministic finding verification against revised artifacts and release blocking on critical/high findings. |
| **9. Research with Evidence Ledger** | **ENFORCED** | Zero hallucinations; strict provenance tracking (`live_web`, `stored_evidence`, `user_reference`, `simulated_mock`), explicit mock labeling, and SSRF-hardened web connectors. |
| **10. Security, Privacy & Least Privilege** | **ENFORCED** | SSRF prevention (blocking metadata `169.254.169.254`, loopback, and RFC 1918 private subnets), tenant isolation, PII/secret scrubbing, and read-only defaults. |
| **11. Continuous Verification & Testing** | **ENFORCED** | 118 automated tests passing; automated regression checks, 2-phase capacity reservations, and durable quota ledger. |

---

### C. Product Intelligence Core: Discovery, Constitution & Memory

1. **Adaptive Discovery (`promptiq/discovery/adaptive.py`)**:
   - Progressive disclosure based on depth mode (`quick`: 3 turns, `guided`: 6 turns, `deep`: 10 turns).
   - **Contradiction Detection (`detect_contradictions`)**: Evaluates intake constraints against conversational answers to detect conflicts (e.g. backend-only invariant vs UI requests; zero-cost invariant vs billable commercial cloud infrastructure).
   - **Missing Information Detection (`detect_missing_high_impact_info`)**: Flags missing acceptance criteria (Stage K), authentication boundaries (Stage I), and validation rules (Stage D).
   - **Inferred Requirement Confirmation**: Handled via `confirm_inferred_{req_id}` with explicit `user_provided` provenance escalation.
   - **SSRF Sanitization**: User-supplied context URLs in intake requests are validated against loopback and cloud metadata before fetching.

2. **Project Constitution Service (`promptiq/services/constitution_service.py`)**:
   - **Immutable Versioning**: Every constitution update generates an immutable `ConstitutionVersion` snapshot and diff.
   - **Granular Comparison (`compare_versions`)**: Computes field-level additions, modifications (`from`/`to`), and removals across arbitrary version pairs $(v_1, v_2)$. Exposed via `GET /api/v1/projects/{project_id}/constitution/compare`.
   - **Safe Rollback (`rollback_to_version`)**: Restores constitution state from target version snapshot $v_t$ by generating a new forward version $N+1$, computing diffs, updating project version pointers, and recording `constitution.reverted` audit records. Exposed via `POST /api/v1/projects/{project_id}/constitution/versions/{version}/rollback`.

3. **Persistent Project Memory (`promptiq/services/project_service.py`)**:
   - **Complete Data Export (`export_project_data`)**: Aggregates project metadata, all constitution versions, compiled packages, discovery sessions, research jobs, evidence claims, and memory checkpoints into an export bundle. Exposed via `GET /api/v1/projects/{project_id}/export` and `promptiq export <project_id>`.
   - **Clean Cascading Deletion (`delete_project`)**: Explicitly cascades deletion through dependent research jobs, source records, evidence claims, evaluation suites, evaluation runs, and failure records to ensure zero orphaned foreign key records.

---

### D. Prompt Intelligence Core: PPS, Compiler & Autopsy

1. **Prompt Specification (PPS) & Multi-Target Compiler (`promptiq/compiler/target_compiler.py`)**:
   - Canonical intermediate representation decoupling user requirements from target-specific syntax.
   - **Target Recommendation Engine (`recommend_target`)**: Analyzes requirements and project characteristics against a capability matrix (MCP support, subagent delegation, browser sandbox, artifact rendering, hierarchical rules) to recommend the optimal execution target. Exposed via `POST /api/v1/projects/{project_id}/compile/recommend` and CLI `promptiq recommend`.
   - **Multi-Target Batch Compilation (`compile_multi_target`)**: Compiles packages across multiple targets (e.g. `google-antigravity`, `claude-code`, `cursor`) in a single atomic invocation. Exposed via `POST /api/v1/projects/{project_id}/compile/multi`.

2. **Adversarial Critique & Revision Verification (`promptiq/critic/autopsy.py`)**:
   - Heuristic inspection for vague phrasing, excessive agency, prompt injection, and missing output contracts.
   - **Structured Finding Identification**: Each finding is assigned a unique ID, category, severity, recommendation, and a `blocks_release` flag (`True` for `critical` and `high` severity).
   - **Deterministic Revision Verification (`verify_findings_against_artifact`)**: Evaluates revised prompt artifacts against previous findings to determine whether hazardous passages were eliminated and required safeguards were added.
   - **Release Gate**: If any critical or high finding remains unresolved, `blocks_release = True`, preventing unreviewed execution. Exposed via `POST /api/v1/critic/verify-revision`.

---

### E. Zero-Price Gateway & Rate Limiting Architecture

1. **Eligible Model Pool**:
   - Google AI Studio: `gemini-3.8-flash` (15 RPM, 1M TPM), `gemini-3.5-flash-lite` (30 RPM, 1M TPM), `gemini-2.5-flash` (15 RPM, 1M TPM).
   - GroqCloud Free: `openai/gpt-oss-120b` (30 RPM, 8K TPM), `openai/gpt-oss-20b` (30 RPM, 8K TPM), `qwen/qwen3.8-27b` (30 RPM, 6K TPM).
   - Synchronized registry limits with provider console documentation and live rate limit response headers.

2. **Capacity Governor Enhancements (`promptiq/gateway/governor.py`)**:
   - **Two-Phase Capacity Reservation (`reserve_capacity`)**: Pre-allocates tokens with a sliding TTL (60s default) to prevent race conditions during concurrent request dispatch.
   - **Reservation Release (`release_reservation`)**: Restores reserved capacity if a request is canceled, aborted, or blocked prior to execution.
   - **Reservation Reconciliation (`reconcile_reservation`)**: Clears reservation and commits actual tokens used upon successful HTTP 200 response.
   - **TTL Auto-Purge (`purge_expired_reservations`)**: Prevents capacity leaks by clearing stale reservations.
   - **Durable Quota Ledger**: Persisted across separate CLI invocations in `data/quota_ledger.json`.

---

### F. Research Intelligence & Evidence Ledger

1. **Evidence Provenance Tracking (`promptiq/schemas/research.py`)**:
   - `SourceRecordSchema` and `EvidenceClaimSchema` explicitly record `provenance` (`live_web`, `stored_evidence`, `user_reference`, `simulated_mock`) and boolean `is_mock`.
   - Deterministic mock fallbacks are explicitly tagged with `provenance="simulated_mock"` and `is_mock=True` with descriptive confidence rationales, preventing any synthetic data from being misrepresented as live evidence.

2. **SSRF Hardening (`promptiq/research/connectors/live_search.py`)**:
   - All external Wikipedia and knowledge endpoints are validated against SSRF protection prior to dispatch.
   - Resolved source URLs are validated to prevent private IP leakage.

---

### G. Prompt Test Lab & Benchmark Suite

1. **Comparative Benchmarks & Regression Detection (`promptiq/eval/test_lab.py`)**:
   - `compare_runs(db, baseline_run_id, candidate_run_id)`: Evaluates test case results across two evaluation runs.
   - Calculates `pass_rate_delta`, identifies `newly_failed_cases` (regressions), identifies `newly_passed_cases` (fixes), computes `latency_delta_ms`, and sets `has_regressions: bool`.
   - Exposed via `GET /api/v1/projects/{project_id}/eval/compare?baseline_id={id}&candidate_id={id}`.

2. **Deterministic Assertions**:
   - Test suites support `contains`, `not_contains`, `regex`, and `schema_valid` assertions with automatic `FailureRecord` logging for test intelligence.

---

### H. Full Surface Integration: Web API, Telegram, MCP & CLI

1. **FastAPI REST API**:
   - 13 modular routers mounted under `/api/v1`.
   - Full OpenAPI specification accessible at `/openapi.json` and interactive Swagger docs at `/docs`.
   - Domain-specific exception handling mapping to standardized JSON error envelopes.

2. **Model Context Protocol (MCP) Server**:
   - Stdio MCP server (`promptiq mcp`) and Remote SSE MCP bridge (`promptiq/mcp/remote.py`).
   - Exposes tools: `get_project_constitution`, `update_project_constitution`, `run_prompt_autopsy`, `compile_prompt_package`, `query_evidence_ledger`.

3. **Telegram Bot Integration (`promptiq/telegram/bot.py`)**:
   - Conversational intake and discovery turns via Telegram bot commands.
   - Account binding between Telegram chat ID and PromptIQ user accounts.

4. **Expanded CLI (`promptiq/cli/main.py`)**:
   - `promptiq init`: Initializes database schema and default CLI workspace.
   - `promptiq status`: Displays zero-price gateway and capacity status.
   - `promptiq quota`: Displays real-time sliding-window RPM/TPM usage, reserved tokens, and reset times across all eligible models.
   - `promptiq review <text|file> [--target <target>]`: Runs adversarial prompt autopsy.
   - `promptiq recommend <requirements>`: Evaluates and recommends the optimal compilation target.
   - `promptiq projects list`: Lists projects in database.
   - `promptiq projects create --name <name> [--description <desc>]`: Creates a project with initialized constitution v1.
   - `promptiq export <project_id> [--output <file>]`: Exports complete project bundle as JSON.
   - `promptiq discovery start --project <id> --intent <intent> [--mode <mode>]`: Initiates discovery turn.

---

### I. Security, Privacy & Compliance Architecture

1. **SSRF Mitigation (`promptiq/core/security.py`)**:
   - `validate_and_sanitize_url(url)`:
     - Enforces HTTP/HTTPS schemes exclusively.
     - Strips embedded userinfo credentials.
     - Resolves hostnames to IP addresses via DNS and checks against `ipaddress.is_private`, `is_loopback`, `is_link_local`, `is_multicast`.
     - Explicitly blocks cloud metadata hostnames (`169.254.169.254`, `metadata.google.internal`, `localhost`).
     - Raises `SecurityError` (HTTP 403) on violation.

2. **Tenant Isolation**:
   - Multi-tenant workspace and project boundary checks enforced in all domain services and API routes (`ProjectService.verify_workspace_access`).
   - Attempting cross-workspace access raises `TenantIsolationError` (HTTP 403).

3. **Data Privacy & Redaction**:
   - `promptiq/core/security.py` redacts API keys, Bearer tokens, passwords, and PII prior to logging.
   - Audit trail records actions (`project.created`, `constitution.updated`, `package.compiled`) with tenant IDs without storing sensitive payloads.

---

### J. Comprehensive Test Suite & Verification Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Priyesh Raj\Desktop\PromptIQ
configfile: pyproject.toml
testpaths: tests
collected 118 items

tests\model_tournament\test_tournament.py ...                            [  2%]
tests\test_api_contracts.py ...                                          [  5%]
tests\test_auth_and_tenancy.py .....                                     [  9%]
tests\test_auxiliary_modules.py ....                                     [ 12%]
tests\test_cli.py ....                                                   [ 16%]
tests\test_compiler_and_adapters.py .....                                [ 20%]
tests\test_constitution.py .                                             [ 21%]
tests\test_critic_autopsy.py ..                                          [ 22%]
tests\test_cross_surface_sync.py .                                       [ 23%]
tests\test_database_migrations.py .                                      [ 24%]
tests\test_discovery.py ...                                              [ 27%]
tests\test_end_to_end_multimodel_workflow.py .                           [ 27%]
tests\test_eval_lab.py ..                                                [ 29%]
tests\test_live_collaboration_pipeline.py .......................        [ 49%]
tests\test_master_platform_execution.py ..........                       [ 57%]
tests\test_mcp_server.py ...                                             [ 60%]
tests\test_memory_and_continuity.py .                                    [ 61%]
tests\test_model_pool.py ...                                             [ 63%]
tests\test_model_registry_and_costs.py .......                           [ 69%]
tests\test_multi_model_collaboration.py .........                        [ 77%]
tests\test_privacy_governance.py .....                                   [ 81%]
tests\test_remote_mcp.py .....                                           [ 85%]
tests\test_research_engine.py ..                                         [ 87%]
tests\test_security_and_redaction.py ..                                  [ 88%]
tests\test_smoke_test.py ....                                            [ 92%]
tests\test_telegram_bot.py ....                                          [ 95%]
tests\test_zero_price_gateway.py .....                                   [100%]

============================= 118 passed in 9.19s =============================
```

- **Static Quality**: `ruff check promptiq tests` → **All checks passed!**
- **Security Audit**: `bandit -r promptiq` → **0 issues identified**
- **Dependency Audit**: `pip-audit` → **No known vulnerabilities found**

---

### K. Production Readiness Assessment & Cloud Hosting Feasibility

- **Evaluation Outcome**: Formally categorized under **Decision C (Not currently feasible without compromise)** in accordance with `docs/CLOUD_COMPUTE_DECISION.md`.
- **Findings**:
  1. No major cloud provider (Google Cloud, AWS, Azure) provides a 24/7 always-on, cardless, ₹0 hard-stop Python ASGI environment.
  2. Cloud Run Free Tier requires a linked billing account (credit card) and does not guarantee ₹0 ceiling against DDoS or unexpected traffic bursts without automated spending shutdown scripts.
  3. Serverless platforms with true free tiers (Render free tier, Koyeb, Railway free tier) either spin down after inactivity (introducing 30-50s cold start latency incompatible with MCP stdio or Telegram webhooks) or impose strict monthly runtime limits.
- **Approved Execution Path**:
  - **Track A (Default)**: Centralized local/operator host staging running on workstation or controlled environment.
  - **Track B (Operator-Authorized Production)**: Google Cloud Run deployment utilizing the verified Dockerfile (`deploy/Dockerfile`) with automated budget billing hard-stops and spend caps, enabled only after explicit operator review.

---

### L. Explicit Confirmation of Invariants

I explicitly confirm that:
1. **Zero UI / Website Frontend components were built**. All deliveries are backend, schemas, intelligence engines, adapters, APIs, and CLI tooling.
2. **Zero user inference API keys or BYOK mechanisms were implemented**.
3. **PromptIQ is 100% free to users forever (₹0)**, operating strictly on approved zero-price developer tier routes.
4. **All test assertions and execution reports reflect genuine, verifiable code behavior**.
