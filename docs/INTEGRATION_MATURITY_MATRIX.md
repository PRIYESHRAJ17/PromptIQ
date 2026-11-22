# PromptIQ — Surface Integration Maturity Matrix

**Version**: 3.0.0  
**Updated**: 2026-11-22  
**Test Reference**: `tests/test_surface_integration_maturity.py`, `tests/test_api_contracts.py`, `tests/test_remote_mcp.py`

---

## 1. Executive Summary

PromptIQ provides a unified prompt intelligence and workflow engine accessible across five distinct operational surfaces:
1. **REST API (FastAPI v1)**
2. **Model Context Protocol (MCP) Server**
3. **Command Line Interface (CLI)**
4. **Telegram Companion Bot**
5. **Python Asynchronous SDK**

All surfaces share the same underlying database schema, Project Constitution, Prompt Specification (PPS v2.0), Model Gateway, and Capacity Governor. A project created or modified in any surface is instantly synchronized across all others.

---

## 2. Integration Maturity Taxonomy

- **Level 1 (Stub)**: Type signatures declared without functional implementation.
- **Level 2 (Experimental)**: Basic workflows work; missing error handling, auth, or concurrency protections.
- **Level 3 (Functional)**: End-to-end workflows validated; automated test coverage; operational in staging.
- **Level 4 (Near Production)**: Hardened against security vulnerabilities, rate limits, and concurrent access.
- **Level 5 (Production-Grade)**: Comprehensive test suite, full telemetry, OpenAPI/JSON-RPC schema compliance, security audits passed.

---

## 3. Surface Maturity Matrix

| Surface | Maturity Level | Protocol / Transport | Auth Mechanism | Tenancy Model | Test Evidence | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REST API** | **Level 5 (Production-Grade)** | HTTP/1.1 & HTTP/2 (FastAPI) | JWT Bearer Tokens | Row-level `user_id` / `workspace_id` | `tests/test_api_contracts.py` | Fully operational, 32 endpoints, OpenAPI 3.1.0 schema generated |
| **MCP Server** | **Level 4 (Near Production)** | stdio, SSE, Streamable HTTP | Local STDIO / Bearer Token | Workspace-scoped session | `tests/test_mcp_server.py`, `tests/test_remote_mcp.py` | Standard MCP 1.0 tools (`start_discovery`, `get_constitution`, `compile_package`, `run_autopsy`) |
| **Terminal CLI** | **Level 4 (Near Production)** | Native Terminal (Click / Rich) | Config file / Stored JWT | Local user profile binding | `tests/test_cli.py` | Interactive terminal UI, colored tables, progress indicators, full workflow commands |
| **Telegram Bot**| **Level 4 (Near Production)** | Telegram Bot API (Webhook + Polling) | Signed HMAC Linking Tokens | Telegram Chat ID mapped to PromptIQ User | `tests/test_telegram_bot.py`, `tests/test_telegram_dedup_concurrency.py` | Account linking, project status, conversational discovery continuation, database-backed persistent webhook replay deduplication (`TelegramProcessedUpdate`, migration `0002`) |
| **Python SDK** | **Level 3 (Functional)** | Async HTTP (`httpx`) | API Token / Bearer Token | User session client context | `tests/test_surface_integration_maturity.py` | Typed client, discovery builder, package compiler, evaluation runner |

---

## 4. Deep-Dive Surface Specifications

### 4.1 FastAPI REST API (Level 5 — Production-Grade)
- **Endpoints**: 32 registered endpoints spanning `/auth`, `/projects`, `/discovery`, `/constitution`, `/compiler`, `/critic`, `/eval`, `/governor`, `/telemetry`.
- **Schema**: Validated OpenAPI 3.1.0 specification persisted in `docs/openapi.json`.
- **Security & Tenancy**: Mandatory dependency injection (`get_current_user`, `get_db`). All queries enforce strict workspace membership checks. IDOR probing across tenants returns HTTP 403/404.
- **Performance**: Async database operations via SQLAlchemy 2.0 with connection pooling.

### 4.2 Model Context Protocol (MCP) Server (Level 4 — Near Production)
- **Supported Transports**:
  - `stdio`: Direct JSON-RPC 2.0 standard input/output for desktop AI agents (Antigravity, Claude Desktop, Cursor).
  - `sse`: Server-Sent Events over HTTP for long-lived agent connections.
  - `streamable_http`: Chunked HTTP streaming for distributed MCP bridges.
- **Security**: Origin header validation (`validate_mcp_origin`) prevents DNS rebinding and cross-site scripting attacks from web agents.
- **Available Tools**:
  - `promptiq_discover`: Starts or continues discovery interview.
  - `promptiq_get_constitution`: Retrieves versioned Project Constitution.
  - `promptiq_compile_target`: Compiles PPS v2 into target-native format.
  - `promptiq_run_autopsy`: Performs heuristic and adversarial prompt inspection.
  - `promptiq_evaluate`: Executes deterministic and multi-run Test Lab evaluations.

### 4.3 Terminal CLI (Level 4 — Near Production)
- **Tooling**: Built with `click` and `rich`.
- **Commands**:
  - `promptiq auth login / register / whoami`
  - `promptiq projects list / create / get`
  - `promptiq discover [quick|guided|deep]`
  - `promptiq compile --target [antigravity|cursor|claude-code|codex|gemini-cli|raw-prompt]`
  - `promptiq autopsy --package-id <id>`
  - `promptiq evaluate --suite-id <id>`
  - `promptiq collaborate --task <task>` (with `--resume` support for rate-limited workflows)
  - `promptiq serve` (starts local FastAPI and MCP daemon)

### 4.4 Telegram Companion Bot (Level 4 — Near Production)
- **Integration Flow**:
  1. User issues `/link` in CLI or Web API, receiving a time-limited cryptographically signed HMAC token.
  2. In Telegram, user sends `/start <token>`.
  3. The backend validates the HMAC token using constant-time comparison and links `telegram_chat_id` to `user_id`.
- **Webhook Hardening & Durability**:
  - `X-Telegram-Bot-Api-Secret-Token` validation rejects unauthorized HTTP requests.
  - Database-backed deduplication (`TelegramProcessedUpdate` table + Alembic migration `0002_add_telegram_processed_updates.py`) with nested transaction savepoints catching race-condition `IntegrityError`s and high-speed L1 cache, preventing duplicate processing across concurrent workers, processes, and restarts.
- **Commands**: `/start`, `/projects`, `/status`, `/review`, `/build`, conversational discovery continuation, `/help`.

### 4.5 Python Async SDK (Level 3 — Functional)
- **Class**: `promptiq.sdk.client.PromptIQClient`.
- **Capabilities**:
  - Full async/await API wrapping all REST endpoints.
  - Typed Pydantic request and response models.
  - Automated Bearer token renewal and error mapping into typed Python exceptions (`AuthenticationError`, `ZeroPriceViolationError`, `QuotaExhaustedError`).
