# PromptIQ Integration & Verification Status Ledger

**Audit Date**: November 21, 2026 (Phase 3.3 Production Feasibility Release)  
**Auditor**: Systems Integration & Verification Engineer  
**Core Invariant**: Absolute honesty in verification status. Never claim live verification without an active live connection. Never manufacture benchmark scores.

---

## 1. Unified Integration Reality Matrix

| Component | Target Interface / Protocol | Verification Status | Verification Evidence & Scope | Operational Action Required |
| :--- | :--- | :--- | :--- | :--- |
| **SQLite (Async)** | Local file `sqlite+aiosqlite:///` | **`VERIFIED`** | 80/80 automated pytest cases passing. Full async transaction, foreign key, and JSON column tests. | None (Ready for local dev/test). |
| **Alembic Migrations** | PostgreSQL DDL script generation | **`VERIFIED`** | Verified programmatic upgrade and downgrade in `tests/test_database_migrations.py`. | None. |
| **PostgreSQL (Neon)** | Cloud Serverless `postgresql+asyncpg://` | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | SQLAlchemy 2.0 async engine configured with `pool_pre_ping=True` and `pool_recycle=300`. Docker daemon and live DB not on workstation PATH. | Provide live Neon database URL in `.env` (`DATABASE_URL`). |
| **Google Gemini API** | Google AI Studio Developer API | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | `GeminiInferenceAdapter` implemented. Free tier zero-price route verified ($0/token). Developer API terms audited (human review on free tier; GENERAL data only; 18+ audience only). | Provide operator key in `.env` (`OPERATOR_GEMINI_API_KEY`). |
| **GroqCloud Free Tier** | Groq OpenAI-compatible Chat API | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | `GroqInferenceAdapter` implemented with candidate models (`openai/gpt-oss-120b`, `20b`, `qwen3.8-27b`). Free tier quotas (30 RPM, 1,000 RPD) strictly enforced. Developer plan paid limits excluded. | Provide operator key in `.env` (`OPERATOR_GROQ_API_KEY`). |
| **OpenRouter Free Tier** | OpenRouter Chat Completions | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | `OpenRouterInferenceAdapter` implemented for `:free` tagged routes. Cardless accounts capped at 50 RPD. | Provide operator key in `.env` (`OPERATOR_OPENROUTER_API_KEY`). |
| **Telegram Bot** | Telegram Cloud Bot API Webhook | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | Webhook handler, timing-safe secret check (`secrets.compare_digest`), update deduplication, and discovery routing verified in `tests/test_telegram_bot.py`. | Provide live bot token in `.env` (`TELEGRAM_BOT_TOKEN`). |
| **Remote MCP Service** | Streamable HTTP / SSE / JSON-RPC | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | Remote SSE, Streamable HTTP protocol handshake, origin security, and stdio client bridge verified in `tests/test_remote_mcp.py`. | Deploy container to remote host with public TLS endpoint. |
| **Internal Deterministic Engine** | In-Memory Deterministic Engine | **`VERIFIED`** | Active on local workstation; verified across 20 benchmark categories and complete 16-step lifecycle. Safe for RESTRICTED compliance data. | None. |

---

## 2. Model Registry Status: Active Candidates vs Retired Models

### Active Verified Zero-Price Candidates (Late 2026)
- `gemini-3.8-flash` (Google AI Studio Developer API: 15 RPM / 1,500 RPD / 1M TPM)
- `gemini-3.5-flash-lite` (Google AI Studio Developer API: 30 RPM / 1,500 RPD / 1M TPM)
- `gemini-2.5-flash` (Google AI Studio Developer API: 15 RPM / 1,500 RPD / 1M TPM)
- `openai/gpt-oss-120b` (GroqCloud Free Tier: 30 RPM / 1,000 RPD / 100k TPD)
- `openai/gpt-oss-20b` (GroqCloud Free Tier: 30 RPM / 14,400 RPD / 500k TPD)
- `qwen/qwen3.8-27b` (GroqCloud Free Tier: 30 RPM / 1,000 RPD / 100k TPD)
- `promptiq-mock-v1` (Internal deterministic in-memory engine: unlimited)

### Permanently Retired / Shut Down Models (Fail-Closed)
- `llama-3.3-70b-versatile` (Retired on GroqCloud endpoints in 2026)
- `llama-3.1-8b-instant` (Retired on GroqCloud endpoints in 2026)
- `qwen-2.5-coder-32b` (Retired on GroqCloud endpoints in 2026)
- `gemini-2.0-flash` (Shut down June 1, 2026)
- `gemini-2.0-flash-lite` (Shut down June 1, 2026)
- `gemini-1.5-flash` / `gemini-1.5-pro` (Shut down September 2025)

---

## 3. Fail-Safe Collaboration Guarantees
1. **Never Mask Live Failure with Mock Success**: When calling live external providers, network or quota failures trigger fail-closed circuit breakers and record `verification_passed=False`.
2. **Failed Critic Fails the Audit**: In `MultiModelCollaborationPipeline`, a failed or timed-out critic sets `verification_passed=False`, `consensus_status="critic_failed"`, and `final_status="FAILED"`.
3. **Limitation Disclosed**: When only a single provider family is available, the audit record openly declares `consensus_status="single_provider_disclosed"`.
4. **Privacy Airgap**: For `RESTRICTED` data, external generative LLM synthesis is refused and structural invariant verification runs in-memory.
