# PromptIQ Integration & Verification Status Ledger

**Audit Date**: November 22, 2026 (Phase 3.4.2 Production Verification Release)  
**Auditor**: Systems Integration & Verification Engineer  
**Core Invariant**: Absolute honesty in verification status. Never claim live verification without an active live connection. Never manufacture benchmark scores.

---

## 1. Unified Integration Reality Matrix

| Component | Target Interface / Protocol | Verification Status | Verification Scope & Current Reality | Operational Action Required |
| :--- | :--- | :--- | :--- | :--- |
| **SQLite (Async)** | Local file `sqlite+aiosqlite:///` | **`VERIFIED`** | 85/85 automated pytest cases passing. Full async transaction, foreign key, and JSON column tests. | None (Ready for local dev/test). |
| **Alembic Migrations** | PostgreSQL DDL script generation | **`VERIFIED`** | Verified programmatic upgrade and downgrade in `tests/test_database_migrations.py` across 22 tables. | None. |
| **PostgreSQL (Neon)** | Cloud Serverless `postgresql+asyncpg://` | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | SQLAlchemy 2.0 async engine configured with `pool_pre_ping=True` and `pool_recycle=300`. Zero live calls to Neon cloud made yet. | Provide live Neon database URL in `.env` (`DATABASE_URL`). |
| **Groq Live Smoke Test** | Safe Opt-In CLI Utility | **`VERIFIED`** | `promptiq.gateway.smoke_test` verified: blocks uncredentialed calls with `BLOCKED_EXTERNAL` without falling back to mock. Secure launcher: `scripts/run_groq_smoke_secure.ps1`. | Run `scripts\run_groq_smoke_secure.ps1 -OptIn -ConfirmFreePlan`. |
| **GroqCloud Free Tier** | Groq OpenAI-compatible Chat API | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | `GroqInferenceAdapter` implemented for `openai/gpt-oss-120b` and `20b`. Free quotas strictly enforced (1,000 RPD, 8k TPM, 200k TPD). Zero credentials configured in current test run. | Provide operator key in `.env` (`OPERATOR_GROQ_API_KEY` or `GROQ_API_KEY`). |
| **Google Gemini API** | Google AI Studio Developer API | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | `GeminiInferenceAdapter` implemented. Qualified as `CONDITIONALLY_ELIGIBLE` due to minor restrictions (<18) and free-tier training terms. | Provide operator key in `.env` (`OPERATOR_GEMINI_API_KEY`). |
| **Cloud Run Compute** | Managed Container Runner | **`REJECTED_FOR_STRICT_ZERO_COST`** | Lacks native zero-latency $0.00 hard stop; billing latency exposes operator to potential unexpected spend; requires credit card. | Rejected for cardless ₹0 production. |
| **Cloudflare Workers** | Edge Ingress / WAF Proxy | **`VERIFIED_AS_PROXY_ONLY`** | 100k req/day free, DDoS protection, edge caching. Ineligible for Python backend due to 10ms CPU and no raw TCP sockets for asyncpg. | Configure Cloudflare as edge reverse proxy. |
| **Telegram Bot** | Telegram Cloud Bot API Webhook | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | Webhook handler, timing-safe secret check (`secrets.compare_digest`), update deduplication, and discovery routing verified in `tests/test_telegram_bot.py`. | Provide live bot token in `.env` (`TELEGRAM_BOT_TOKEN`). |
| **Remote MCP Service** | Streamable HTTP / SSE / JSON-RPC | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | Remote SSE, Streamable HTTP protocol handshake, origin security, and stdio client bridge verified in `tests/test_remote_mcp.py`. | Deploy container to remote host with public TLS endpoint. |
| **Internal Deterministic Engine** | In-Memory Deterministic Engine | **`VERIFIED`** | Active on local workstation; verified across 20 benchmark categories, 10 pilot cases, and complete lifecycle. Safe for RESTRICTED compliance data. | None. |

---

## 2. Model Registry Status: Active Candidates vs Retired Models

### Active Verified Zero-Price Models (Late 2026)
- `openai/gpt-oss-120b` (GroqCloud Free Tier: 30 RPM / 1,000 RPD / 8k TPM / 200k TPD) — Primary Reasoning / Generator
- `openai/gpt-oss-20b` (GroqCloud Free Tier: 30 RPM / 1,000 RPD / 8k TPM / 200k TPD) — Fast Burst / Critic Specialist
- `promptiq-mock-v1` (Internal deterministic in-memory engine: unlimited) — RESTRICTED Airgap Engine

### Conditionally Eligible Models (Requires Condition Verification)
- `gemini-3.8-flash` / `3.5-flash-lite` / `2.5-flash` (Google AI Studio: adult developer environments only, strictly 18+)
- `@cf/meta/llama-3.1-8b-instruct` (Cloudflare Workers AI: 10,000 Neurons/day free, edge classifier role only)
- `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter: 50 RPD limit on cardless accounts)

### Isolated Evaluation Preview Models (Barred from Production Routing)
- `qwen/qwen3.8-27b` (GroqCloud Preview Model: isolated to evaluation environments per Phase 3.4 directive)

### Permanently Retired / Shut Down Models (Fail-Closed)
- `gemini-2.0-flash` / `gemini-2.0-flash-lite` (Shut down June 1, 2026)
- `gemini-1.5-flash` / `gemini-1.5-pro` (Shut down September 2025)
- `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` / `qwen-2.5-coder-32b` (Retired on GroqCloud endpoints in 2026)

---

## 3. Fail-Safe Collaboration Guarantees
1. **Never Mask Live Failure with Mock Success**: When calling live external providers, network or quota failures trigger fail-closed circuit breakers and record `verification_passed=False`.
2. **Failed Critic Fails the Audit**: In `MultiModelCollaborationPipeline`, a failed or timed-out critic sets `verification_passed=False`, `consensus_status="critic_failed"`, and `final_status="FAILED"`.
3. **Limitation Disclosed**: When only a single provider family is available, the audit record openly declares `consensus_status="single_provider_disclosed"`.
4. **Privacy Airgap**: For `RESTRICTED` data, external generative LLM synthesis is refused and structural invariant verification runs in-memory.
