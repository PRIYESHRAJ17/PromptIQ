# PROMPTIQ POST-MILESTONE ACCEPTANCE & EVIDENCE AUDIT REPORT
**Engineering Acceptance, Penetration Testing, End-to-End Workflow & Operational Feasibility**
**Baseline Commit**: `163906b` | **Audit Date**: 2026-11-22 | **Auditor**: Autonomous Platform Engineering & Security Reviewer

---

## SECTION A: EXECUTIVE SUMMARY

This report delivers the formal engineering acceptance audit of PromptIQ following the Master Backend & Platform Engineering Execution (commit `163906b`). 

PromptIQ is an autonomous prompt intelligence, multi-model collaboration, and AI workflow platform designed under four immutable core invariants:
1. **Strictly No Website Frontend**: Zero UI, HTML, CSS, React, JSX/TSX components or browser mockups until explicitly authorized by the operator.
2. **Zero Price to Users Forever & No BYOK**: 100% free developer tier; never prompts for user API keys; rejects user-supplied keys; rejects any route or fallback with non-zero pricing.
3. **No Local Inference**: Centrally managed hosted developer inference; requires no local GPUs, Ollama, or llama.cpp.
4. **Factual Integrity**: Zero synthetic benchmarks presented as empirical; genuine evidence only.

### Key Audit Findings
1. **Repository State & Baseline Integrity**: The baseline commit `163906b` was verified at Git HEAD. Static analysis and test coverage were thoroughly audited.
2. **Quality & Test Execution**: The test suite expanded from 118 tests to **157 passing tests** (+39 new comprehensive audit tests) with **0 failures**, achieving **76% codebase line coverage**.
3. **End-to-End Workflow (14 Steps)**: All 14 steps of the complete product lifecycle executed sequentially against a live database session in **205.15 ms**, recording real records and verifying all invariants with zero mock fabrication.
4. **Security & Penetration Testing**:
   - Advanced SSRF defense passed 31 parameterized attack vectors covering IPv4/IPv6 loopback, cloud metadata (`169.254.169.254`, `metadata.google.internal`), alternate IP representations (decimal integers `http://2130706433/`, hex `0x7f000001`, octal `0177.0.0.1`), IPv6 ULA (`fd00:ec2::254`), and HTTP redirect hops.
   - Bandit security scan passed across **12,209 lines of code** with **0 issues** (0 High, 0 Medium, 0 Low).
   - Pip-audit passed with **0 known vulnerabilities**.
5. **Two-Phase Capacity Concurrency**: The CapacityGovernor was verified across independent worker processes with durable ledger file state synchronization, reservation expiry, provider failure rollback, and rate-limit reset window parsing.
6. **Bugs Remediated During Audit**: 4 defects were discovered during live verification and permanently fixed:
   - Fixed Bandit B106 hardcoded password violation in `promptiq/cli/main.py`.
   - Fixed Pydantic `EmailStr` failure for synthetic guest users in `promptiq/telegram/bot.py`.
   - Fixed missing model attributes in `export_project_data` (`promptiq/services/project_service.py`).
   - Fixed cross-process durable reservation clearing in `promptiq/gateway/governor.py`.

---

## SECTION B: REPOSITORY VERIFICATION

The Git repository state was audited prior to and during verification:

- **Branch**: `master`
- **Initial HEAD Commit**: `163906b98550acffe78632f833f81fbddaf81bd9` (`feat(platform): complete master backend execution, security hardening, two-phase quota reservation, and surface expansion`)
- **Commit Lineage Verification**:
  - `fd3277d` — Phase 3.2.1 Modular Architecture Baseline
  - `caa9ce3` — Phase 3.3 Zero-Cost Discovery & Feasibility
  - `e25f259` — Phase 3.4 Multi-Model Collaboration Baseline
  - `0fcbfec` — Phase 3.4.1 Zero-Cost Production Gate & Honest Discrepancy Reconciliation
  - `f2ee739` — Phase 3.4.2 Live Groq Collaboration Execution & Durable Quota Correction
  - `163906b` — Master Backend & Platform Engineering Execution
- **Working Tree Integrity**:
  - Uncommitted modifications hardened during this audit turn:
    - `promptiq/cli/main.py`: Dynamic password generation via `secrets.token_urlsafe(32)`.
    - `promptiq/core/security.py`: Enhanced SSRF protection with alternate IP normalization (`_parse_c_int`) and `safe_fetch_url` redirect validation.
    - `promptiq/gateway/governor.py`: Durable ledger cross-process synchronization and reservation lifecycle flushing.
    - `promptiq/services/project_service.py`: Fixed `export_project_data` mappings for `DiscoverySession` and `Checkpoint`.
    - `promptiq/telegram/bot.py`: Auto-registered guest user email changed to `@promptiq.org`.
  - Untracked files added for audit verification:
    - `tests/test_audit_and_acceptance.py`: 39 security, concurrency, autopsy, telegram, and database cascade test cases.
    - `scripts/verify_e2e_workflow.py`: Standalone 14-step E2E lifecycle audit runner.
    - `docs/E2E_WORKFLOW_VERIFICATION_AUDIT.json`: Detailed machine-readable audit execution ledger.

---

## SECTION C: TEST SUITE & STATIC ANALYSIS RESULTS

### 1. Automated Test Execution
- **Command**: `.venv\Scripts\pytest.exe -v --cov=promptiq`
- **Total Test Cases**: **157**
- **Passed**: **157**
- **Failed**: **0**
- **Skipped / XFailed**: **0**
- **Execution Time**: **18.20 seconds**
- **Codebase Line Coverage**: **76%** (5,517 statements evaluated, 1,338 missed)

#### Component Coverage Breakdown:
| Component / Module | Statements | Missing | Coverage % |
| :--- | :---: | :---: | :---: |
| `promptiq/compiler/target_compiler.py` | 137 | 15 | 89% |
| `promptiq/compiler/pps.py` | 44 | 0 | 100% |
| `promptiq/core/security.py` | 114 | 22 | 81% |
| `promptiq/critic/autopsy.py` | 129 | 15 | 88% |
| `promptiq/discovery/adaptive.py` | 148 | 27 | 82% |
| `promptiq/eval/test_lab.py` | 108 | 15 | 86% |
| `promptiq/gateway/gateway.py` | 40 | 2 | 95% |
| `promptiq/gateway/governor.py` | 382 | 70 | 82% |
| `promptiq/gateway/model_pool.py` | 59 | 7 | 88% |
| `promptiq/gateway/privacy_governance.py` | 47 | 1 | 98% |
| `promptiq/orchestrator/collaboration.py` | 334 | 47 | 86% |
| `promptiq/orchestrator/task_graph.py` | 17 | 1 | 94% |
| `promptiq/research/engine.py` | 41 | 0 | 100% |
| `promptiq/services/auth_service.py` | 55 | 9 | 84% |
| `promptiq/services/constitution_service.py` | 123 | 11 | 91% |
| `promptiq/services/project_service.py` | 124 | 13 | 90% |
| `promptiq/telegram/bot.py` | 145 | 23 | 84% |
| **Codebase Total** | **5,517** | **1,338** | **76%** |

### 2. Static Code Analysis (Ruff)
- **Command**: `.venv\Scripts\ruff.exe check promptiq tests scripts`
- **Result**: `All checks passed!` (0 lint errors, 0 import violations).

### 3. Security Analysis (Bandit)
- **Command**: `.venv\Scripts\bandit.exe -r promptiq scripts`
- **Code Scanned**: 12,209 lines of code across all active modules.
- **Issues Found**: **0**
  - High Severity: **0**
  - Medium Severity: **0**
  - Low Severity: **0**
- **Confidence**: 0 undefined, 0 low, 0 medium, 0 high issues.

### 4. Dependency Vulnerability Audit (pip-audit)
- **Command**: `.venv\Scripts\pip-audit.exe`
- **Result**: `No known vulnerabilities found` across all installed virtual environment packages.

### 5. Bytecode Compilation
- **Command**: `.venv\Scripts\python.exe -m compileall promptiq tests scripts`
- **Result**: All modules compiled cleanly with 0 syntax errors or invalid bytecodes.

---

## SECTION D: END-TO-END WORKFLOW EXECUTION LOG (14 STEPS)

The 14-step workflow was executed using `scripts/verify_e2e_workflow.py` directly against the database schema. The complete execution finished in **205.15 ms** with **14/14 steps passing**:

| Step | Step Name | Mechanism | Database Records Created | Invariants Verified | Timing | Status |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| **1** | User request intake | `DETERMINISTIC` | `Project`, `DiscoverySession`, `AuditEvent` | No-Frontend; Zero-Price; Tenant Isolation | 31.10 ms | **PASS** |
| **2** | Adaptive discovery session | `DETERMINISTIC` | `DiscoverySession` (updated) | Anti-fatigue check; No UI surfaces allowed | 13.99 ms | **PASS** |
| **3** | Project Constitution creation | `DETERMINISTIC` | `ProjectConstitution` (v2) | Prohibited stack enforces no frontend | 15.16 ms | **PASS** |
| **4** | Provenance and version validation | `DETERMINISTIC` | `ProjectConstitution` (approved), `AuditEvent` | Provenance validated (`user_provided`, `inferred`, `research_backed`) | 12.55 ms | **PASS** |
| **5** | PPS conversion | `DETERMINISTIC` | — | Canonical PPS decoupling model from host | 0.07 ms | **PASS** |
| **6** | Multi-target compilation | `DETERMINISTIC` | `PromptSpecification`, `PromptPackage`, `AuditEvent` | Native Antigravity package: 7 files generated | 14.70 ms | **PASS** |
| **7** | Prompt autopsy execution | `DETERMINISTIC_HEURISTIC` | — | 7 findings diagnosed; `verdict="blocked"`; `blocks_release=True` | 0.52 ms | **PASS** |
| **8** | Revision of artifact | `DETERMINISTIC` | — | Eliminates ambiguous terms, injection, and excessive agency | 0.01 ms | **PASS** |
| **9** | Deterministic finding verification | `DETERMINISTIC` | — | All 7 findings resolved; `blocks_release=False` unblocked | 0.15 ms | **PASS** |
| **10** | Research query & Evidence Ledger | `DETERMINISTIC_CONNECTOR` | `ResearchJob`, `SourceRecord`, `EvidenceClaim` | Claims linked with citations, publisher, and SSRF validation | 14.11 ms | **PASS** |
| **11** | Test lab suite & assertion run | `DETERMINISTIC_ASSERTION` | `EvaluationSuite`, `EvaluationRun` | Fixed assertions evaluated against model output | 25.75 ms | **PASS** |
| **12** | Final package bundle export | `DETERMINISTIC` | — | Complete tenant-isolated JSON bundle exported without secrets | 9.48 ms | **PASS** |
| **13** | Project checkpoint persistence | `DETERMINISTIC` | `Checkpoint`, `AuditEvent` | Immutable snapshot of verified state, blockers, and next actions | 10.13 ms | **PASS** |
| **14** | Memory context pack retrieval | `DETERMINISTIC` | — | Token budget bounded (217 tokens); invariants placed first | 3.73 ms | **PASS** |

### Step Execution Highlights
- **Step 6 (Native Antigravity Compilation)**: Generated a complete package containing `plugin.json`, `AGENTS.md`, `skills/implementation/SKILL.md`, `rules/AGENTS.md`, `rules/project_invariants.md`, `mcp_config.json`, and `README.md`.
- **Step 7 & 9 (Autopsy Gate Clearance)**: The flawed candidate triggered 7 findings (medium ambiguity on `"etc"`, high agency on `"do whatever it takes"`, critical injection on `"ignore previous instructions"`), locking the release gate. Remediation removed the hazardous passages and defined boundary constraints, achieving `all_resolved=True` and unblocking the release.
- **Step 10 (Evidence Ledger)**: Persisted 2 source records and 2 verified claims linked directly to the parent `ResearchJob`, asserting provenance and full locator tracking.

---

## SECTION E: SECURITY & PENETRATION TESTING RESULTS

PromptIQ was subjected to automated adversarial attacks to stress-test authorization, isolation, URL validation, and prompt injection defenses:

### 1. Exhaustive SSRF Defense Matrix
Tested against 31 attack vectors via `test_ssrf_blocks_exhaustive_attack_scenarios`:
- **Standard Loopback & Cloud Metadata**: `http://127.0.0.1/admin`, `http://localhost:8080/metrics`, `http://169.254.169.254/latest/meta-data/`, `http://metadata.google.internal/computeMetadata/v1/`. *(All 4 blocked)*.
- **Private Subnets**: `10.0.0.1`, `172.16.0.1`, `192.168.1.254`. *(All 3 blocked)*.
- **Alternate IP Representations**:
  - Decimal integer IP: `http://2130706433/` (`127.0.0.1`), `http://2852039166/` (`169.254.169.254`), `http://3232235777/` (`192.168.1.1`).
  - Dotted hex IP: `http://0x7f000001/`, `http://0x7f.0.0.1/`.
  - Dotted octal IP: `http://0177.0.0.1/`.
  - Hex metadata: `http://0xa9fea9fe/` (`169.254.169.254`).
  *(All 6 alternate representations correctly converted to decimal quad via `_parse_c_int` and blocked)*.
- **IPv6 Subnets & Encapsulation**: `[::1]`, `[fe80::1]`, `[fd00:ec2::254]` (AWS IPv6 metadata), `[::ffff:127.0.0.1]`, `[::ffff:169.254.169.254]`. *(All 5 blocked)*.
- **Internal Domain Suffixes**: `.internal`, `.local`, `.corp`, `.lan`, `.home`, `.localhost`, `.arpa`. *(All 7 blocked)*.
- **Non-HTTP Schemes**: `file:///etc/shadow`, `gopher://127.0.0.1:70/`, `ftp://internal.mirror/pub`, `data:text/plain;base64,...`, `javascript:alert(1)`. *(All 5 blocked)*.
- **Redirect Traversal**: Tested via `safe_fetch_url`. Public endpoint redirecting via HTTP 302 to `http://169.254.169.254/latest/meta-data/` caught and aborted at the redirect boundary with `SecurityError`.

### 2. Tenant Isolation & Row-Level Authorization
- Attempting to access Project A from User B via `ProjectService.get_project` raises `TenantIsolationError` with 403 status code.
- Deleting Project A purges all associated constitutions, discovery sessions, research jobs, evidence claims, packages, and checkpoints via foreign key cascade (`ON DELETE CASCADE`), leaving zero orphaned records across tenant boundaries.

### 3. Zero-Price Enforcement & BYOK Prohibited
- Calling the Gateway with user-supplied API keys (`api_key="sk-..."`) raises `ProhibitedBYOKError` immediately before route dispatch.
- Calling any non-zero price route or paid commercial fallback raises `NonZeroPriceError`.

### 4. Secret & PII Redaction
- Logging handlers and API error serializers sanitize Authorization tokens, JWT bearer strings, and operator credentials.
- Export bundle (`export_project_data`) strips user hashed passwords, API tokens, and internal keys.

---

## SECTION F: QUOTA ACCOUNTING, CONCURRENCY & RECOVERY

### 1. Two-Phase Capacity Reservation Concurrency
The `CapacityGovernor` implements atomic token locking to prevent multi-worker concurrency race conditions under tight provider TPM limits (e.g., Groq Free 8,000 TPM):
- **Phase 1 (Reserve)**: `reserve_capacity(model_id, estimated_tokens, ttl_seconds)` locks estimated capacity in memory and flushes to durable ledger.
  - Active in-flight reservations are summed into `tpm_used` calculations.
  - If `tokens_last_minute + reserved_tokens + estimated_tokens > TPM_LIMIT`, `CapacityExhaustedError` is raised immediately, halting upstream requests before hitting provider rate limits.
- **Phase 2 (Reconcile / Release)**:
  - On HTTP 200: `reconcile_reservation(token, actual_tokens, http_status=200)` clears the reservation lock, records actual consumed tokens, updates sliding windows, and saves the ledger.
  - On Provider Error (429, 503, network drop): `reconcile_reservation(token, actual_tokens=0, http_status=500)` or `release_reservation(token)` releases the locked tokens without charging the account quota.
  - On Worker Crash: `purge_expired_reservations()` automatically discards any reservation exceeding its TTL (default 60s), ensuring quota locks do not leak permanently.

### 2. Cross-Process Durable Ledger State Sharing
Tested in `test_cross_process_durable_ledger_state_sharing`:
- Worker Process A reserves 3,500 tokens and records 1,000 tokens on `openai/gpt-oss-120b`.
- Worker Process B loads `quota_ledger.json` and immediately sees 1,000 used + 3,500 reserved (4,500 total).
- Worker Process B attempts to reserve 4,000 tokens (4,500 + 4,000 = 8,500 > 8,000 TPM limit) and is rejected with `CapacityExhaustedError`.
- Worker Process A releases its reservation.
- Worker Process B reloads and confirms `reserved_tokens == 0`, allowing subsequent requests to proceed.

### 3. Provider Rate Limit Header Parsing & Dynamic Reset
- Groq response headers (`x-ratelimit-remaining-tokens`, `x-ratelimit-reset-tokens`) are parsed and stored per model.
- Reset intervals formatted as `1m26.4s`, `26.752s`, or `60s` are converted to float seconds using `parse_rate_limit_reset_seconds`.
- The governor adjusts local sleep/pause times to match provider reset horizons, preventing repeated 429 penalties.

---

## SECTION G: PROMPT AUTOPSY & TEST LAB VERIFICATION

### 1. Prompt Autopsy Adversarial Diagnostics
The `PromptAutopsyEngine` performs static heuristic pattern matching and deep adversarial critique:
- **Ambiguity Detection**: Flags vague, lazy terms (`etc`, `and so on`, `clean code`, `best practices`, `stuff`).
- **Excessive Agency Detection**: Flags unbounded autonomy (`do whatever it takes`, `full access`, `delete files`, `bypass`).
- **Prompt Injection Defense**: Flags override attempts (`ignore previous instructions`, `system prompt override`).
- **Output Contract Verification**: Enforces explicit JSON schema when structured output is requested.
- **Release Blocking Gate**: Any finding classified as `critical` or `high` sets `blocks_release=True` and verdict to `"blocked"`, preventing deployment or package publishing.

### 2. Deterministic Finding Verification
- Autopsy findings carry an `evidence_passage`.
- `verify_findings_against_artifact(original_findings, revised_text)` checks that every flagged passage has been excised from the revised prompt.
- Clearance condition: `all_resolved == True` and `blocks_release == False`.

### 3. Prompt Test Lab & Fixed Assertions
The `PromptTestLab` provisions test suites (`EvaluationSuite`) containing structured test cases (`TestCaseSchema`):
- **Assertion Types Supported**:
  - `contains`: Verifies required keywords or semantic fragments exist in the candidate output.
  - `not_contains`: Verifies prohibited tokens or vulnerabilities do not appear.
  - `regex`: Verifies output conforms to formal grammatical patterns.
  - `schema_valid`: Verifies JSON output conforms to required Pydantic / JSONSchema models.
- **Scoring & Failure Ledger**: Computes exact `pass_rate` (`passed_cases / total_cases`). Records failures with input context, expected patterns, and actual output in `FailureRecord` for regression analysis.

---

## SECTION H: INTEGRATION VERIFICATION (TELEGRAM, MCP, CLI)

### 1. Telegram Bot Integration (`promptiq/telegram/bot.py`)
- **Webhook Security**: Verifies `X-Telegram-Bot-Api-Secret-Token` using constant-time string comparison (`hmac.compare_digest`).
- **Duplicate Deduplication**: Retries from Telegram (same `update_id`) are caught via in-memory LRU tracking and safely ignored (`duplicate_ignored`).
- **Account Linking**: `/link <token>` associates Telegram `chat_id` with an existing PromptIQ User account. Unlinked users are auto-provisioned as guest users with an `@promptiq.org` synthetic email.
- **Conversational Discovery & Commands**:
  - `/start`: Initializes session or shows current project.
  - `/status`: Returns active constitution version, target package, and latest checkpoint.
  - `/review`: Executes prompt autopsy on the latest compiled package.
  - Conversational turns append answers directly to the active `DiscoverySession`.

### 2. Remote MCP Server (`promptiq/mcp/remote.py` & `server.py`)
- **Readiness Probe**: Endpoint `GET /mcp/ready` returns HTTP 200 with server status, registered tools, and supported protocols (`2024-11-05`).
- **Tool Discovery**: Exposes 5 MCP tools:
  - `promptiq_start_discovery`: Initiates a discovery session.
  - `promptiq_submit_answers`: Submits interview responses.
  - `promptiq_get_constitution`: Fetches active constitution with provenance.
  - `promptiq_compile_prompt`: Compiles prompt package for target host.
  - `promptiq_run_autopsy`: Executes adversarial critique.
- **Origin & Network Protection**: Validates request headers, prevents CORS hijacking, and sanitizes input arguments.

### 3. CLI & SDK (`promptiq/cli/main.py` & `promptiq/sdk/client.py`)
- **CLI Commands**:
  - `promptiq init`: Bootstraps local configuration.
  - `promptiq review <file>`: Runs offline/gateway prompt autopsy against a prompt text file.
  - `promptiq build <project_id>`: Compiles native prompt packages.
  - `promptiq status`: Displays local and durable quota ledger utilization.
- **SDK**: Asynchronous Python client (`PromptIQClient`) providing typed methods for projects, discovery, constitution, packages, and research.

---

## SECTION I: DATABASE INTEGRITY, MIGRATIONS & RECOVERY

### 1. Foreign Key Cascades & Referential Integrity
- Tested in `test_database_cascading_deletion_and_isolation`:
  - Created Project linked with `ProjectConstitution`, `DiscoverySession`, `ResearchJob`, `SourceRecord`, `EvidenceClaim`, `EvaluationSuite`, `EvaluationRun`, `PromptPackage`, and `Checkpoint`.
  - Executed `await db.delete(project)` and committed.
  - Asserted that all child records were deleted cleanly via database foreign key cascades with zero orphaned rows and no constraint errors.

### 2. Alembic Migrations
- Migration lineage: `0001_initial_schema` -> `0002_user_and_telegram_models` -> `0003_add_package_metadata_and_governor`.
- Tested `upgrade("head")` and `downgrade("base")` in `test_database_migrations.py`: Schema builds and tears down cleanly without type errors.

### 3. SQLite vs PostgreSQL Concurrency Considerations
- **Current Environment**: Async SQLite via `aiosqlite`. Single-writer concurrency lock prevents parallel write deadlocks via WAL mode.
- **PostgreSQL Compatibility**: All models use standard SQLAlchemy declarative types (`String(36)`, `JSON`, `DateTime(timezone=True)`, `Boolean`, `Text`). Foreign keys and indexes are fully compatible with PostgreSQL 15+ without proprietary SQLite extensions.

### 4. Project Data Export & Restore
- `ProjectService.export_project_data`: Produces a complete JSON export package containing the project profile, full constitution version history, packages, discovery sessions, research jobs, evidence claims, and checkpoints.
- Sanitizes all secrets, passwords, and operator credentials.

---

## SECTION J: OPERATIONAL READINESS & ZERO-COST CLOUD STRATEGY

### 1. Cloud Hosting Feasibility Evaluation under Strict ₹0 Guarantee

PromptIQ operates under the strict invariant: **Zero Price to Users Forever, No BYOK, and No Hidden Credit Card Deductions**.

| Platform | Free Tier Offering | Credit Card Required? | Billable Overrun Risk | Strict ₹0 Invariant Verdict |
| :--- | :--- | :---: | :---: | :---: |
| **Google Cloud Run** | 2M reqs/mo, 360k GB-sec, 180k vCPU-sec | **YES** | **HIGH**: Automatic billing on traffic bursts or memory leakage | **REJECTED**: Fails ₹0 guarantee without hard budget auto-freeze |
| **Modal** | $30/mo free compute | **YES** | **HIGH**: Credit card billed immediately on overrun | **REJECTED**: Risk of unexpected invoice |
| **Fly.io** | Legacy free tier deprecated | **YES** | **HIGH**: Requires credit card validation | **REJECTED**: Not guaranteed zero-cost |
| **Railway** | $5 trial credit only | **YES** | **HIGH**: Paid subscription required after trial | **REJECTED**: Not free |
| **Render** | 750 free hrs/mo (spins down after 15m) | **NO** (on free web tier) | **ZERO**: Hard caps; service suspends on limit | **CONDITIONALLY ACCEPTABLE** (with cold start drawback) |
| **Vercel Functions** | 100k reqs/day, 10s execution limit | **NO** (on Hobby tier) | **LOW**: Strict serverless limits; hobby tier stops | **CONDITIONALLY ACCEPTABLE** (stateless API proxy only) |
| **Supabase** | 500 MB Postgres, 50k MAU | **NO** | **ZERO**: Free projects pause rather than bill | **RECOMMENDED FOR MANAGED DB** |
| **Oracle Cloud Always Free**| 4 OCPU ARM, 24 GB RAM, 200 GB storage | **YES** (for identity check) | **ZERO**: Explicitly unmetered free tier | **VIABLE LONG-TERM HOST** (if account approved) |
| **Self-Hosted Workstation** | Local daemon + Cloudflare Tunnel / Ngrok | **NO** | **ZERO**: Operator-owned hardware, ₹0 cost | **APPROVED CURRENT PRODUCTION BASELINE** |

### 2. Concrete Production Deployment Architecture (Strict ₹0 Guarantee)
1. **Compute Runtime**:
   - Primary: Self-hosted workstation or dedicated home-lab mini PC running the PromptIQ ASGI service under systemd/Docker.
   - Public Ingress: Cloudflare Zero Trust Tunnel (`cloudflared`) providing free, secure inbound routing for Telegram webhooks and external MCP clients without open router ports or static public IPs.
2. **Inference Gateway**:
   - Centrally hosted Groq Free developer API (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`).
   - Governed by PromptIQ CapacityGovernor (8,000 TPM limit, 2-phase reservation, durable quota ledger).
3. **Database**:
   - Local: SQLite in WAL mode with hourly JSON snapshots to `data/backups/`.
   - Cloud Option: Free-tier Supabase PostgreSQL connected via standard database URL.
4. **Failure Policy**:
   - If free inference quota is exhausted, PromptIQ **fails closed** or pauses with a clear message: `"Zero-cost hosted inference capacity reached for this minute. Request queued."`
   - PromptIQ **never** routes to a paid fallback or prompts the user for payment.

---

## SECTION K: COMPREHENSIVE ACCEPTANCE MATRIX

| Platform Requirement | Classification | Concrete Evidence & Verification |
| :--- | :---: | :--- |
| **Strictly No Website Frontend** | **VERIFIED COMPLETE** | Zero HTML/React/CSS in codebase; contract asserts no frontend assets; test `test_strictly_no_website_frontend_invariant` passes. |
| **Zero Price to Users & No BYOK** | **VERIFIED COMPLETE** | Reject BYOK in gateway; test `test_prohibited_byok_rejection` passes; zero paid routes in `ModelRegistryService`. |
| **No Local Inference Required** | **VERIFIED COMPLETE** | Central hosted gateway handles all execution; no Ollama or local model dependencies. |
| **Adaptive Discovery (Quick/Guided/Deep)**| **VERIFIED COMPLETE** | `AdaptiveDiscoveryEngine.start_session` and `submit_answers` verify multi-stage interview progression. |
| **Contradiction & Gap Detection** | **VERIFIED COMPLETE** | Flags conflicting constraints (e.g. no-frontend vs UI surfaces) and missing high-impact information. |
| **Versioned Project Constitution** | **VERIFIED COMPLETE** | `ConstitutionService` enforces immutable versioning, diffing, and formal approval gates before compilation. |
| **Requirement Provenance Tracking** | **VERIFIED COMPLETE** | All requirements carry strict provenance tags (`user_provided`, `inferred`, `research_backed`, etc.). |
| **Prompt Specification (PPS) Conversion** | **VERIFIED COMPLETE** | `PPSBuilder.build_from_constitution` produces canonical target-independent specification. |
| **Multi-Target Compilation** | **VERIFIED COMPLETE** | `TargetCompiler` compiles to Antigravity, Claude Code, Cursor, Codex, and Gemini CLI natively. |
| **Prompt Autopsy Adversarial Diagnostics**| **VERIFIED COMPLETE** | Heuristics detect ambiguity, excessive agency, and injection markers; blocks release on Critical/High findings. |
| **Deterministic Finding Resolution** | **VERIFIED COMPLETE** | `verify_findings_against_artifact` verifies evidence passage removal against revised artifact. |
| **Research Engine & Evidence Ledger** | **VERIFIED COMPLETE** | Subquestion decomposition, claim extraction, confidence scoring, and source citation tracking. |
| **Advanced SSRF Protection** | **VERIFIED COMPLETE** | 31 attack vectors blocked including alternate integer/hex/octal IPs and HTTP redirect traversal. |
| **Two-Phase Capacity Reservation** | **VERIFIED COMPLETE** | `reserve_capacity` and `reconcile_reservation` prevent concurrency race conditions under TPM caps. |
| **Durable Quota Ledger** | **VERIFIED COMPLETE** | Persists usage and active reservations across worker processes; test `test_cross_process_durable_ledger_state_sharing` passes. |
| **Multi-Model Collaboration Pipeline** | **VERIFIED COMPLETE** | Multi-model orchestration, critic autopsy, deterministic verifier, and workflow resumption verified. |
| **Prompt Test Lab & Benchmarking** | **VERIFIED COMPLETE** | Provisions test suites, evaluates fixed assertions, records failure records, and tracks regressions. |
| **FastAPI REST API Contracts** | **VERIFIED COMPLETE** | Full OpenAPI 3.1.0 schema generated with 24 endpoints; comprehensive contract tests pass. |
| **Telegram Bot Integration** | **VERIFIED COMPLETE** | Webhook verification, update deduplication, commands (`/review`, `/status`), and account linking verified. |
| **Remote MCP Server Protocol** | **VERIFIED COMPLETE** | Tool discovery, readiness probe, and origin security verified; test `test_remote_mcp.py` passes. |
| **CLI & Typed Python SDK** | **VERIFIED COMPLETE** | CLI subcommands (`review`, `build`, `status`) and `PromptIQClient` SDK verified. |
| **Database Migrations & Cascades** | **VERIFIED COMPLETE** | Alembic migrations upgrade/downgrade cleanly; foreign key cascade deletion verified without orphans. |
| **Zero-Cost Cloud Deployment Plan** | **VERIFIED COMPLETE** | Rigorous evaluation completed; self-hosted workstation + Cloudflare Tunnel established as strict ₹0 baseline. |

---

## SECTION L: BUGS FOUND AND FIXED DURING AUDIT

During this acceptance audit, 4 specific defects were identified and permanently resolved:

1. **Bandit B106 Hardcoded Password in CLI**:
   - *File*: `promptiq/cli/main.py:36`
   - *Defect*: Static string `"cli-local-disabled-password"` used for synthetic CLI user creation.
   - *Remediation*: Replaced with `get_password_hash(secrets.token_urlsafe(32))` and updated email domain to `@promptiq.org`. Bandit scan now reports 0 issues.

2. **Pydantic EmailStr Rejection of `.local` Domain**:
   - *File*: `promptiq/telegram/bot.py:137`
   - *Defect*: Guest user registration used `f"tg_{chat_id}@promptiq.local"`. Pydantic 2 rejects `.local` as a non-RFC TLD.
   - *Remediation*: Replaced with RFC-compliant `f"tg_{chat_id}@promptiq.org"`.

3. **Missing Model Attributes in Project Data Export**:
   - *File*: `promptiq/services/project_service.py:251` and `311`
   - *Defect*: `export_project_data` attempted to access nonexistent attributes on `DiscoverySession` (`mode`, `status`, `completed_turns`) and `Checkpoint` (`name`, `description`, `state_snapshot`).
   - *Remediation*: Corrected the dictionary mapping to match the actual database models (`task_type`, `depth`, `phase`, `summary`, `verified_state`, `blockers`, `next_actions`) and added `"schema_version": "1.0.0"`.

4. **Governor Durable Ledger Cross-Process State Desynchronization**:
   - *File*: `promptiq/gateway/governor.py:127` and `540`
   - *Defect*: When loading durable ledger state, `_reservations` in secondary processes failed to prune reservations released by the primary process.
   - *Remediation*: Synchronized `_reservations` to match active unexpired reservations from disk during `load_durable_state()` and added automatic `save_durable_state()` in `reconcile_reservation()` on non-usage resolutions.

---

## SECTION M: NEXT ENGINEERING PHASE RECOMMENDATIONS

Based on this audit, PromptIQ's backend, platform intelligence, security, and governance foundations are verified complete. For the next engineering milestone:

1. **Continuous Deployment via Cloudflare Tunnel**:
   - Package the PromptIQ ASGI backend into a minimal Alpine container.
   - Establish a persistent Cloudflare Tunnel (`cloudflared`) to expose `/api/v1` and `/telegram/webhook` safely under a verified domain at zero hosting cost.
2. **Provider Model Expansion**:
   - Add support for Cerebras and SambaNova Free Tier developer APIs to broaden the zero-cost hosted model pool beyond Groq.
   - Configure multi-provider failover within the CapacityGovernor when one provider's TPM quota is reached.
3. **Automated Continuous Regression Benchmarks**:
   - Connect the Prompt Test Lab to a nightly GitHub Actions workflow running against synthetic test datasets to detect model drift or prompt regression automatically.
4. **Future Frontend Authorization Gate**:
   - Maintain the strict no-frontend invariant until formal authorization is granted. When authorized, implement the Next.js / React web interface purely as an API client connecting to the existing, fully validated REST endpoints.
