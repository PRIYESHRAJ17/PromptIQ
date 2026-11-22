# PromptIQ Operations Runbook

**Audience**: DevOps, SRE, and System Operators  
**Scope**: Operational maintenance, monitoring, alert handling, incident remediation, and quality gate execution for PromptIQ infrastructure.  
**Version**: 3.0.0  
**Updated**: 2026-11-22  

---

## 1. Core Health & Metrics Probes

| Endpoint | Target Component | Purpose | Healthy Response |
| :--- | :--- | :--- | :--- |
| `GET /health` | FastAPI Container | Container Liveness probe | `200 OK` with `{"status": "healthy"}` |
| `GET /ready` | Database & Engine | Load Balancer Readiness probe | `200 OK` with `{"status": "ready"}` |
| `GET /api/v1/metrics` | Prometheus Metrics | Telemetry, request counts, errors | Prometheus text exposition |
| `GET /api/v1/governor/quota` | Capacity Governor | Quota remaining, circuit breaker state | JSON with `rpm_remaining`, `is_paused` |

---

## 2. Standard Operating Procedures (SOP)

### SOP-01: Zero-Price Route Monitoring & Quota Exhaustion
- **Trigger**: `GET /api/v1/governor/quota` indicates `rpm_remaining < 2` or upstream provider returns `429 Too Many Requests`.
- **System Action**: The `CapacityGovernor` automatically engages the circuit breaker and activates fail-closed protection. Non-critical requests are queued or paused.
- **Operator Action**:
  1. Inspect `/api/v1/governor/quota` for the active pause reason.
  2. If the primary route is throttled, verify if `MANAGED_INFERENCE_PRIMARY_ROUTE` can route eligible requests to secondary GroqCloud without exceeding Groq's 100k daily token limit.
  3. **DO NOT** attach a paid billing key or enable paid overages. PromptIQ must fail-closed rather than charge users.

### SOP-02: Executing Acceptance Scenarios & Quality Gates
- **Trigger**: Prior to release tagging or after major code changes.
- **Procedure**:
  ```powershell
  .venv\Scripts\python.exe scripts/run_acceptance_scenarios.py
  ```
- **Acceptance Verification**:
  - Total scenarios executed must be **10**.
  - Blocked count must be **0**.
  - Failed count must be **0**.
  - Overall verdict must be `PASS` or `CONDITIONAL_PASS`.
  - Audit traces are written to `docs/ACCEPTANCE_SCENARIOS_TRACE.json`, `docs/ACCEPTANCE_SCENARIOS_TRACE_V2.json`, and `docs/ACCEPTANCE_SCENARIOS_TRACE_V3.json`.

### SOP-03: Quota Ledger Maintenance & Unsticking
- **Trigger**: A crashed process leaves stale locks or reservations in `data/quota_ledger.json`.
- **Procedure**:
  1. Inspect `data/quota_ledger.json` for pending reservations older than 60 seconds.
  2. The `CapacityGovernor` automatically purges reservations exceeding their TTL on next invocation.
  3. To perform a manual reset of rolling windows during development staging:
     ```powershell
     .venv\Scripts\python.exe -c "from promptiq.gateway.governor import CapacityGovernor; gov = CapacityGovernor(); gov.reset_local_ledger()"
     ```

### SOP-04: Emergency Circuit Breaker Manual Trip / Reset
- **Trip Circuit Breaker**:
  If an upstream provider behaves erratically or changes their terms:
  ```powershell
  .venv\Scripts\python.exe -c "from promptiq.gateway.governor import CapacityGovernor; gov = CapacityGovernor(); gov.trip_circuit_breaker(reason='Manual operator intervention')"
  ```
- **Reset Circuit Breaker**:
  ```powershell
  .venv\Scripts\python.exe -c "from promptiq.gateway.governor import CapacityGovernor; gov = CapacityGovernor(); gov.reset_circuit_breaker()"
  ```

### SOP-05: Database Migrations & Schema Deployment
- **Trigger**: New release deployed with schema modifications.
- **Procedure**:
  1. Set the database connection URL:
     ```powershell
     $env:DATABASE_URL="sqlite+aiosqlite:///./data/promptiq.db"  # Or PostgreSQL URL
     ```
  2. Inspect pending migrations:
     ```powershell
     .venv\Scripts\alembic.exe check
     ```
  3. Apply migration upgrade:
     ```powershell
     .venv\Scripts\alembic.exe upgrade head
     ```
  4. Verify current migration head:
     ```powershell
     .venv\Scripts\alembic.exe current
     ```

### SOP-06: Operator Secret Rotation
- **Frequency**: Every 90 days or immediately upon suspected compromise.
- **Procedure**:
  1. Generate new JWT secret using cryptographically secure random bytes:
     ```powershell
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
  2. Update environment variable `SECRET_KEY` in deployment configuration or Google Secret Manager.
  3. Trigger rolling restart of backend service. Existing client tokens will expire naturally upon expiration of their TTL.

### SOP-07: Telegram Webhook Diagnostic & Repair
- **Trigger**: Telegram companion does not respond to `/start` or `/projects`.
- **Procedure**:
  1. Check webhook status with Telegram API:
     ```bash
     curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
     ```
  2. Verify:
     - `url` matches `https://<domain>/api/v1/telegram/webhook`.
     - `has_custom_certificate` is false.
     - `pending_update_count` is 0 or low.
     - `last_error_message` is null or resolved.
  3. If broken, re-register webhook via `setWebhook` with configured `X-Telegram-Bot-Api-Secret-Token`.

---

## 3. Incident Severity Levels & Response Times

| Severity | Definition | Target Response | Target Resolution |
| :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Zero-price breach detected; unauthorized external billable route called; security vulnerability exploited. | < 15 minutes | < 2 hours (Immediate circuit breaker trip) |
| **SEV-2 (Major)** | All free inference routes exhausted; multi-model collaboration failing; database down. | < 30 minutes | < 4 hours |
| **SEV-3 (Minor)** | Single target compiler failing; non-critical telemetry reporting issue; Telegram webhook retry lag. | < 4 hours | < 24 hours |
| **SEV-4 (Informational)**| Documentation discrepancy; test suite warning; minor advisory autopsy finding. | Next business day | Next scheduled sprint |
