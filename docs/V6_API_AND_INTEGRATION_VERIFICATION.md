# PROMPTIQ V6 — API AND INTEGRATION VERIFICATION REPORT

## Executive Overview

PromptIQ provides a unified backend powering multiple client surfaces: REST API, Model Context Protocol (MCP) server, Command Line Interface (CLI), Python SDK, and Telegram Bot. This report establishes the exact operational readiness of each surface.

---

## 1. REST API Surface

**Source**: `promptiq/api/main.py`, `promptiq/api/routes/`

- **Endpoints Verified**:
  - `/api/v1/auth`: Login, registration, token refresh, API key creation.
  - `/api/v1/projects`: Project CRUD, listing, soft-delete.
  - `/api/v1/constitution`: Get, update, rollback, and impact analysis.
  - `/api/v1/discovery`: Intake, adaptive question answering, sufficiency scoring.
  - `/api/v1/specs`: PPS generation, validation, and retrieval.
  - `/api/v1/packages`: Target-native instruction compilation.
  - `/api/v1/autopsy`: 21-mode Prompt Autopsy diagnostic execution.
  - `/api/v1/eval`: Test Lab benchmark execution and report generation.
  - `/api/v1/jobs`: Distributed job queue management and status polling.
- **Contract Adherence**: OpenAPI 3.1.0 schema generated and fully compliant (`docs/openapi.json`).
- **Test Evidence**: `tests/test_api_contracts.py` (PASS).

---

## 2. Model Context Protocol (MCP) Server Surface

**Source**: `promptiq/mcp/server.py`

- **Transport**: JSON-RPC 2.0 over standard I/O (`stdio`).
- **Exposed Tools**:
  - `promptiq_discover`: Initiates or advances adaptive discovery.
  - `promptiq_compile_prompt`: Compiles PPS into target-native format.
  - `promptiq_autopsy`: Performs 21-failure-mode prompt inspection.
  - `promptiq_evaluate`: Evaluates prompt or output against Test Lab test cases.
  - `promptiq_search_evidence`: Queries evidence graph for domain facts.
- **Security**: Strict input sanitization; zero BYOK enforcement; rate-limited.
- **Test Evidence**: `tests/test_mcp_server.py`, `tests/test_remote_mcp.py` (PASS).

---

## 3. CLI Subprocess Verification

**Source**: `promptiq/cli/main.py`, `tests/test_cli_subprocess.py`

PromptIQ V6 verified CLI operations through real operating system subprocess execution (`subprocess.run`):
1. `test_cli_subprocess_help`: `promptiq --help` returns exit code 0 and displays commands.
2. `test_cli_subprocess_status`: `promptiq status` reports service state, zero-price status, and database connection.
3. `test_cli_subprocess_quota`: `promptiq quota` displays provider token pools and remaining capacity.
4. `test_cli_subprocess_review_clean_prompt`: `promptiq review "..."` correctly validates compliant prompt and returns exit code 0.
5. `test_cli_subprocess_redaction`: `promptiq review "sk-proj-secret..."` verifies that sensitive keys are redacted in console output.

---

## 4. Python SDK Surface

**Source**: `promptiq/sdk/client.py`

- Asynchronous HTTP client based on `httpx`.
- Implements exponential backoff retries on transient network errors.
- Respects rate-limit headers (`Retry-After`).
- Strongly typed responses using Pydantic schemas.

---

## 5. Telegram Bot Surface

**Source**: `promptiq/telegram/bot.py`

- Long-polling daemon supporting Telegram Bot API.
- Implements `/start`, `/help`, `/project`, `/discover`, `/review`, `/compile`.
- Concurrency deduplication: Redis/in-memory lock prevents processing duplicate update IDs concurrently (`tests/test_telegram_dedup_concurrency.py`).
- Session continuity: Links Telegram `chat_id` to persistent PromptIQ tenant and project memory.
