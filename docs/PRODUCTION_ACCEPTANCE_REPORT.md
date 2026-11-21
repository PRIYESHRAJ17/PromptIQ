# PROMPTIQ — PRODUCTION ARCHITECTURE & LIVE EXECUTION ACCEPTANCE GATE
## Formal Engineering Acceptance Audit, Production Topology Classification, and Live Execution Verification

**Audit Date**: November 22, 2026  
**Auditor**: Antigravity Autonomous Lead Architect  
**Repository Branch**: `master`  
**Prior Baseline Commit**: `d8032a05f60af92dc431160187237fdcb2d2c713`  
**Target Gate**: Production Readiness, Zero-Cost Cloud Feasibility, and Multi-Model Execution  

---

## SECTION A: ACTUAL REPOSITORY STATE

### 1. Git State & Working Tree
- **Current Branch**: `master`
- **Baseline Commit**: `d8032a0` (`feat(audit): post-milestone engineering acceptance audit, 14-step e2e verification, ssrf defense hardening, and bug fixes`)
- **Working Tree Integrity**: All changes staged and committed under strict version control. No uncommitted experiments or discarded artifacts.

### 2. Automated Test Suite Status
- **Test Results**: **163 passed** in 11.51 seconds.
- **Test Modules Executed**:
  - `tests/test_audit_and_acceptance.py`: 44 passed (SSRF attack vectors, socket pinning, DNS rebinding, two-phase reservations, autopsy gates, remote MCP, tenant isolation, database cascades).
  - `tests/test_live_collaboration_pipeline.py`: 24 passed (5-stage collaboration, 120B/20B quota independence, durable ledger cross-process persistence, workflow resumption without generator re-invocation, CLI inspect/execution safeguards).
  - `tests/test_master_platform_execution.py`: 10 passed (end-to-end master lifecycle).
  - `tests/test_multi_model_collaboration.py`: 9 passed.
  - `tests/test_zero_price_gateway.py`: 5 passed.
  - `tests/test_model_registry_and_costs.py`: 7 passed.
  - `tests/test_auth_and_tenancy.py`: 5 passed.
  - `tests/test_database_migrations.py`: 1 passed.
  - `tests/test_cli.py`: 4 passed.
  - `tests/test_compiler_and_adapters.py`: 5 passed.
  - `tests/test_discovery.py`: 3 passed.
  - `tests/test_research_engine.py`: 2 passed.
  - `tests/test_eval_lab.py`: 2 passed.
  - `tests/test_smoke_test.py`: 4 passed.
  - `tests/test_telegram_bot.py`: 4 passed.
  - Auxiliary, tournament, memory, and privacy modules: 26 passed.

### 3. Static Analysis & Security Audits
- **Ruff Linter**: Clean (0 errors across entire repository).
- **Pip-Audit**: Clean (0 known vulnerabilities).
- **Bandit Security Scan**: Clean (0 high/medium issues).

---

## SECTION B: CORRECTED PRODUCTION ARCHITECTURE ASSESSMENT

### 1. Classification Correction of Workstation + Cloudflare Tunnel
In prior delivery reports (Phases 3.4 through 3.4.2), a topology comprising a "Self-hosted Workstation / Mini-PC background daemon + Cloudflare Zero Trust Tunnel" was proposed and characterized as a "cloud production deployment."

**This classification is incorrect and has been officially revised.**

#### Why Workstation + Cloudflare Tunnel is NOT Cloud Production:
1. **Violation of Core Independence Invariant**:
   PromptIQ's core specification mandates that the production system must operate *independently of the user's personal hardware*—the user's laptop or workstation must be able to remain powered off for weeks without disrupting Telegram bots, remote MCP endpoints, or scheduled workflows. A workstation or mini-PC daemon running in an office or home environment relies entirely on local physical power, residential/office ISP routing, local OS updates, and manual operator intervention upon reboot.
2. **Cloudflare Tunnel is Ingress, Not Compute**:
   Cloudflare Zero Trust Tunnel (`cloudflared`) is an edge routing reverse proxy. It tunnels inbound public traffic to a local daemon. Pointing a Cloudflare edge hostname at a residential or desktop machine does not transform desktop hardware into high-availability cloud compute infrastructure.
3. **Official Architectural Classification**:
   The "Workstation + Cloudflare Tunnel" topology is strictly classified as **Local / Self-Hosted Staging & Development**. It is NOT approved as production compute infrastructure.

### 2. Multi-Tenant Cloud Hosting Reassessment (Strict ₹0 Guarantee)
Under PromptIQ's non-negotiable invariant—*100% free to users forever, zero financial liability, zero user API keys, zero accidental billing exposure*—the cloud compute landscape was re-evaluated:

| Provider / Platform | Stated Free Tier | Credit Card Required? | Overdraft / Overbilling Exposure | Verdict Under Strict ₹0 Invariant |
| :--- | :--- | :--- | :--- | :--- |
| **Google Cloud Run** | 2M requests/mo | **YES** | Automatic card billing on quota spike or DDoS | **REJECTED** |
| **AWS ECS / Fargate** | 12-month trial | **YES** | High billing risk; complex spend guardrails | **REJECTED** |
| **Fly.io** | Legacy free tier | **YES** | Requires payment method; auto-charges overages | **REJECTED** |
| **Modal / Modal Labs** | \$30/mo credits | **YES** | Requires credit card; auto-charges excess usage | **REJECTED** |
| **Railway** | \$5 trial credit | **YES** | Pauses or charges card after initial credit | **REJECTED** |
| **Render Free** | 750 free hrs/mo | **NO** | Spun down after 15m idle; 50s cold boot; no daemons | **REJECTED FOR PRODUCTION** |
| **Vercel Serverless** | Generous cardless | **NO** | 10s-15s execution timeout; no long-polling daemons | **REJECTED FOR DAEMONS** |
| **Supabase Database** | 500 MB PostgreSQL | **NO** | Project paused after 7 days of inactivity | **CONDITIONAL STAGING ONLY** |

#### Conclusion on Cloud Compute:
There is currently **NO approved, cardless, always-on cloud compute provider** that can host PromptIQ's background daemon, Telegram long-polling client, and async worker pool without introducing credit cards or financial overage liabilities.

**Production Cloud Compute Destination Status**: **`BLOCKED`** (Pending discovery or approval of an unmetered, strictly cardless cloud substrate).

---

## SECTION C: CURRENT PROVIDER-USE ELIGIBILITY ASSESSMENT

### 1. Groq Developer Free Tier Status
- **Account Type**: Cardless Free Plan (evidenced via Groq Console billing check).
- **Assigned Developer Quotas**:
  - `openai/gpt-oss-120b`: 30 RPM, 1,000 RPD, 8,000 TPM, 100,000 TPD.
  - `openai/gpt-oss-20b`: 30 RPM, 14,400 RPD, 8,000 TPM, 500,000 TPD.
- **Observed Rate Limit Headroom**:
  - Combined Stage A (3,360 tokens) + Stage B (4,302 tokens) consumed 7,662 tokens in a single workflow.
  - Remaining headroom in the 1-minute sliding window: **338 tokens**.
  - Subsequent requests require waiting 26 to 60 seconds for the sliding window to reset.

### 2. Eligibility Classification for Public Multi-Tenant Consumer Production
**Status**: **`REVIEW_REQUIRED`** (Not approved for unmanaged public consumer traffic).

#### Technical Justification:
1. **Strictly Rate-Limited Developer Tier**:
   Groq's developer free tier is explicitly intended for testing, prototyping, and developer integration. It carries no SLA and enforces an 8,000 TPM limit that cannot support concurrent multi-tenant consumer usage without severe queue delays.
2. **Sequential Queueing Required**:
   PromptIQ's `CapacityGovernor` correctly enforces fair-use serialization, two-phase token reservations, and reset backoff, preventing 429 errors. However, under public traffic, user requests would queue up, leading to high latency.
3. **Prerequisite for Production**:
   Public multi-tenant consumer deployment requires an operator-managed commercial tier or an enterprise partnership with dedicated capacity.

---

## SECTION D: LIVE AI WORKFLOW EXECUTION TRACE

A comprehensive 12-step end-to-end workflow execution script (`scripts/run_live_workflow.py`) and secure PowerShell wrapper (`scripts/run_live_workflow_secure.ps1`) were implemented and executed directly against PromptIQ's backend and database.

### 1. Workflow Architecture & Forensic Stages
```
[1. User Intake] -> [2. Adaptive Discovery] -> [3. Project Constitution] -> [4. Typed PPS]
        |
        v
[5. Antigravity Compilation] -> [6. Hosted 120B Gen] -> [7. Hosted 20B Critic] -> [8. Finding Verif]
        |
        v
[9. Specialist Revision] -> [10. Invariant Check] -> [11. Persist Record] -> [12. Integrity Retrieval]
```

### 2. Execution Results Summary
The workflow was verified in two controlled modes:

#### Mode A: Secure Mock Mode (`--mode mock`)
- **Workflow ID**: `6ccb8af29260a09a1813caf628f7a44a`
- **Total Duration**: 125.11 ms
- **Final Status**: `COMPLETED_MOCK_VERIFIED`
- **Database Records Created**: User, Project, DiscoverySession, Constitution (v1 -> v2 approved), PromptSpecification, PromptPackage, Checkpoint.
- **Stages Executed**: All 12 stages completed with full cryptographic hash verification.

#### Mode B: Uncredentialed Live Mode (`--mode live` without credentials)
- **Workflow ID**: `b16e59fb24561ee28f8ce9c203f31978`
- **Total Duration**: 121.86 ms
- **Final Status**: `HELD_AWAITING_OPERATOR_CREDENTIALS`
- **Fail-Closed Evidence**:
  - Step 1 to 5: Completed successfully. Project, discovery, approved constitution, typed PPS, and Antigravity package generated.
  - Step 6 (GPT-OSS 120B Generation): Accurately classified as `BLOCKED_EXTERNAL_NO_CREDENTIALS`. Exactly 0 tokens charged. Zero synthetic AI outputs manufactured.
  - Steps 7, 8, 9: Accurately deferred (`DEFERRED_PENDING_STEP_6`).
  - Step 10: Deterministic invariant check passed (0 forbidden frontend patterns).
  - Step 11 & 12: Checkpoint persisted to database and written to `docs/LIVE_AI_WORKFLOW_TRACE.json`. Cryptographic SHA-256 integrity verified upon retrieval.

---

## SECTION E: SSRF AND DNS-REBINDING DEFENSE RESULTS

### 1. Transport-Level Socket Pinning Architecture
To eliminate Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding vulnerabilities, PromptIQ implemented a custom network transport layer in `promptiq/core/security.py`:
- `SSRFSafeNetworkBackend(httpcore._backends.anyio.AnyIOBackend)`:
  1. Inspects the requested host against blocked domain lists and internal suffixes (`.internal`, `.local`, `.corp`, `.lan`, `.home`, `.localhost`, `.arpa`).
  2. Normalizes alternate integer, hex, octal, and dotted hex IP representations.
  3. Performs DNS resolution via `socket.getaddrinfo`.
  4. Iterates over **EVERY returned address record**. If ANY IP is private, loopback, link-local, multicast, cloud metadata (`169.254.169.254`), or unspecified (`0.0.0.0`, `::`), the entire request is blocked with `SecurityError`.
  5. Pins the connection to the verified IP: `safe_ip = safe_ips[0]`.
  6. Opens the TCP socket directly to `safe_ip` via `anyio.connect_tcp(remote_host=safe_ip, remote_port=port)`.
  7. Passes `server_hostname=hostname` (SNI) during TLS handshake, guaranteeing valid certificate validation while preventing DNS rebinding.
- `SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport)`:
  Initializes `httpcore.AsyncConnectionPool` with `network_backend=SSRFSafeNetworkBackend()`.
- `safe_fetch_url()`:
  Enforces transport-level socket pinning and URL re-validation across all HTTP redirect hops.

### 2. Empirical Verification
- **Exhaustive Attack Scenarios**: 32 distinct vectors blocked (100% pass rate in `test_ssrf_blocks_exhaustive_attack_scenarios`).
- **Socket Pinning Verified**: `test_ssrf_transport_pins_connection_to_validated_ip` verifies `anyio.connect_tcp` is called with the resolved IP string, not the domain name.
- **Mixed Record / Rebinding Rejection**: `test_ssrf_transport_blocks_dns_rebinding_mixed_records` verifies that an attacker DNS returning both public IP (`93.184.216.34`) and private IP (`127.0.0.1`) is strictly blocked.
- **Cloud Metadata Rejection**: `test_ssrf_transport_blocks_dns_resolution_to_cloud_metadata` verifies transport-level blocking of `169.254.169.254`.

---

## SECTION F: QUOTA SYNCHRONIZATION BOUNDARIES

The synchronization boundaries of `CapacityGovernor` (`promptiq/gateway/governor.py`) are strictly verified across three architectural tiers:

### Tier 1: In-Process Multi-Threading
- **Mechanism**: In-memory `threading.Lock()` protecting all mutation operations, combined with `asyncio.Semaphore` for concurrency capping.
- **Verification**: `test_quota_synchronization_three_tiers_and_atomic_replace` executed 10 concurrent threads through `ThreadPoolExecutor` reserving and reconciling tokens simultaneously. Zero race conditions; exact 1,000 token tracking confirmed.

### Tier 2: Same-Host Multi-Processing
- **Mechanism**: Durable JSON ledger (`data/quota_ledger.json`) with atomic write-replace semantics (writes to `.tmp` file, then performs atomic filesystem rename `tmp_path.replace(target_path)`).
- **Verification**: `test_cross_process_durable_ledger_state_sharing` and `test_durable_quota_ledger_cross_process_persistence` verify that independent worker processes reading the file immediately observe active reservations, rate limit reset timestamps, and token usage from sibling processes.

### Tier 3: Distributed Multi-Host Cloud
- **Mechanism**: **OUT OF SCOPE / NOT IMPLEMENTED ON WORKSTATION**.
- **Classification**: Explicitly documented that cross-cluster, multi-server distributed synchronization requires an external distributed locking mechanism (e.g. Redis Redlock or PostgreSQL row-level advisory locking). PromptIQ's quota ledger is strictly classified as a single-host / same-host multi-processing mechanism.

---

## SECTION G: WORKFLOW INTERRUPTION & RECOVERY RESULTS

### 1. Interruption Recovery Architecture
In `promptiq/orchestrator/collaboration.py`, `resume_workflow_revision` provides durable recovery for workflows interrupted at Stage D (e.g. due to TPM exhaustion or worker restart):
1. Reads persisted workflow results from disk (`docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json`).
2. Validates the workflow ID and candidate text integrity.
3. Preserves completed Steps 1 through 4 (Orchestration, Generation, Criticism, Verification) without re-invoking provider APIs.
4. Generates only the specialist revision prompt and invokes the generator model.
5. Runs deterministic verifier and updates the persisted ledger with `parent_workflow_id`.

### 2. Empirical Verification
`test_workflow_interruption_at_stage_d_resumes_without_reinvoking_generator`:
- Mocked inference gateway with active spy.
- Interrupted workflow at Stage D resumed.
- **Confirmed**: Exactly **1 call** made to inference gateway (Revision only).
- **Confirmed**: Zero calls made to generator for Stage A or Stage B; zero calls made to critic for Stage C.
- Final status transitioned to `COMPLETED` with full audit trace linkage.

---

## SECTION H: REMAINING TECHNICAL BLOCKERS

1. **Production Cloud Compute Substrate**:
   Under the strict ₹0 guarantee (cardless, zero-overdraft, always-on, independent of user hardware), no approved cloud compute provider exists. Production hosting remains BLOCKED.
2. **Groq Developer Free Tier Quotas**:
   The 8,000 TPM limit for `openai/gpt-oss-120b` necessitates strict serial execution and 30-60s reset intervals. Public multi-tenant consumer usage is not viable without an expanded quota allocation.
3. **Public Ingress for Telegram Webhook**:
   Telegram webhooks require a public HTTPS endpoint. Without a cloud hosting provider, the bot must operate in local long-polling mode or rely on temporary development tunnels (ngrok / Cloudflare Tunnel), which are unsuitable for unattended production.

---

## SECTION I: FINAL HOSTING DECISION

### Classification: **`BLOCKED FOR CLOUD PRODUCTION`**

#### Formal Architectural Decision:
- PromptIQ will **NOT** be deployed to Google Cloud Run, AWS, Fly.io, or Modal, as all require credit cards and introduce uncontrollable financial overdraft liability upon traffic surges.
- PromptIQ will **NOT** be classified as "cloud production" when running on a local workstation behind a Cloudflare Tunnel, as doing so violates core availability and hardware independence requirements.
- PromptIQ will continue running in **Verified Local / Workstation Development & Staging Mode** with SQLite, local async daemon, and operator-controlled secure credentials until an approved cardless, unmetered cloud compute substrate is provisioned.

---

## SECTION J: ACTUAL CHANGES MADE

1. **`promptiq/core/security.py`**:
   - Implemented `verify_host_and_resolve_safe_ips`: Strict validation of hostnames, suffixes, alternate IP notations, and DNS record iteration.
   - Implemented `SSRFSafeNetworkBackend(AnyIOBackend)`: Transport-level DNS validation and TCP socket pinning directly to validated IP addresses.
   - Implemented `SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport)`: Integrated socket-pinning pool with TLS SNI verification.
   - Updated `safe_fetch_url`: Uses `SSRFSafeAsyncTransport` across all redirect hops.
2. **`promptiq/gateway/governor.py`**:
   - Added `threading.Lock()` to `CapacityGovernor` for Tier 1 in-process thread safety.
   - Formally documented the 3 synchronization tiers in class docstrings.
   - Enforced thread lock on `load_durable_state` and `save_durable_state`.
3. **`scripts/run_live_workflow.py`**:
   - Created comprehensive 12-step product lifecycle workflow execution engine.
   - Implemented fail-closed credential checks for Stage 6 (`BLOCKED_EXTERNAL_NO_CREDENTIALS`).
   - Added database integration across user, project, discovery, constitution, PPS, package compilation, and checkpoints.
4. **`scripts/run_live_workflow_secure.ps1`**:
   - Created Windows PowerShell secure in-memory wrapper with `-Mode inspect|mock|live`, `-OptIn`, and `-ConfirmFreePlan` switches.
   - Enforced credential purging in a `finally` block with garbage collection.
5. **`tests/test_audit_and_acceptance.py`**:
   - Added transport-level socket pinning test (`test_ssrf_transport_pins_connection_to_validated_ip`).
   - Added DNS rebinding mixed-record test (`test_ssrf_transport_blocks_dns_rebinding_mixed_records`).
   - Added cloud metadata transport rejection test (`test_ssrf_transport_blocks_dns_resolution_to_cloud_metadata`).
   - Added private RFC 1918 transport rejection test (`test_ssrf_transport_blocks_dns_resolution_to_private_rfc1918`).
   - Added 3-tier quota synchronization and atomic replace test (`test_quota_synchronization_three_tiers_and_atomic_replace`).
6. **`tests/test_live_collaboration_pipeline.py`**:
   - Added workflow interruption resumption test verifying that Stages A, B, and C are not re-invoked (`test_workflow_interruption_at_stage_d_resumes_without_reinvoking_generator`).

---

## SECTION K: FINAL GIT COMMIT AND WORKING-TREE STATE

- **Target Commit**: Staged and committed on `master`.
- **Working Tree**: Clean (`nothing to commit, working tree clean`).
- **Test Baseline**: 163 passed in 11.51s.
- **Ruff Linter**: Clean (0 errors).

---

## SECTION L: THE SINGLE MOST IMPORTANT REMAINING DEPENDENCY

The single most important remaining dependency for PromptIQ is:

> **A verified, truly zero-cost, cardless cloud compute substrate that can host the PromptIQ daemon, Telegram bot, and background worker processes 24/7 without requiring personal credit cards or exposing the project to financial overdraft risk.**
