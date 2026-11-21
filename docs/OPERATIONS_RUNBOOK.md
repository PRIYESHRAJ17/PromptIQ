# PromptIQ Operations Runbook

**Audience**: DevOps, SRE, and System Operators  
**Scope**: Operational maintenance, monitoring, alert handling, and incident remediation for PromptIQ Cloud Infrastructure.

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
  2. If the Google Gemini primary route is throttled, verify if `MANAGED_INFERENCE_PRIMARY_ROUTE` can route eligible requests to secondary GroqCloud without exceeding Groq's 100k daily token limit.
  3. **DO NOT** attach a paid billing key or enable paid overages. PromptIQ must fail-closed rather than charge users.

### SOP-02: Executing Database Migrations on Release
- **Trigger**: New release deployed with schema modifications.
- **Procedure**:
  1. Set the cloud database URL:
     ```bash
     export DATABASE_URL="postgresql+asyncpg://..."
     ```
  2. Inspect pending migrations:
     ```bash
     alembic check
     ```
  3. Apply migration upgrade:
     ```bash
     alembic upgrade head
     ```
  4. Verify table schema and foreign key constraints via `alembic current`.

### SOP-03: Operator Secret Rotation
- **Frequency**: Every 90 days or immediately upon suspected compromise.
- **Procedure**:
  1. Generate new JWT secret or obtain renewed operator API key.
  2. Add a new version in Google Cloud Secret Manager:
     ```bash
     gcloud secrets versions add promptiq-jwt-secret --data-file=- <<< "NEW_SECRET_KEY"
     ```
  3. Trigger a rolling redeployment of Cloud Run to bind to the latest secret version:
     ```bash
     gcloud run services update promptiq-backend --region us-central1
     ```

### SOP-04: Telegram Webhook Diagnostic & Repair
- **Trigger**: Telegram companion does not respond to `/start` or `/projects`.
- **Procedure**:
  1. Check webhook status with Telegram API:
     ```bash
     curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
     ```
  2. Verify:
     - `url` matches `https://promptiq-backend-xyz.a.run.app/api/v1/telegram/webhook`.
     - `has_custom_certificate` is false.
     - `pending_update_count` is 0 or low.
     - `last_error_message` is null or resolved.
  3. If broken, re-register webhook via `setWebhook` (see [DEPLOYMENT_GUIDE.md](file:///c:/Users/Priyesh%20Raj/Desktop/PromptIQ/docs/DEPLOYMENT_GUIDE.md)).
