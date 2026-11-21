# PromptIQ Disaster Recovery & Business Continuity Plan

**Recovery Time Objective (RTO)**: < 15 minutes  
**Recovery Point Objective (RPO)**: < 1 hour  
**Core Goal**: Restore full cloud-hosted operations without data loss, without relying on user workstations, and while maintaining the ₹0 cost invariant.

---

## 1. Failure Scenarios and Mitigations

| Failure Event | Probability | Impact | Automated Mitigation | Manual Recovery Procedure |
| :--- | :--- | :--- | :--- | :--- |
| **Cloud Run Container Crash** | Low | Transient request drop | Cloud Run automatically replaces failed container instance within 2 seconds. | Inspect Cloud Logging; verify readiness probe via `/ready`. |
| **Neon Compute Outage** | Low | Database read/write unavailable | Neon automatically restarts compute instances upon cold start or node migration. | If regional outage exceeds 15 mins, activate failover to Supabase secondary database. |
| **Primary Inference Outage** | Medium | Gemini API 5xx / 429 errors | `CapacityGovernor` circuit breaker trips; diverts eligible tasks to GroqCloud. | If all providers are down, system enters paused state with user notifications. |
| **GCP Region Outage** | Very Low | Cloud Run unavailable in `us-central1` | None (single region free-tier). | Deploy container image to secondary free-tier region (`us-east1`) via Terraform / gcloud. |
| **Telegram Webhook Dropped** | Low | Delayed bot notifications | Telegram retries webhook delivery exponentially for up to 24 hours. | Verify `getWebhookInfo` and re-register endpoint. |

---

## 2. Database Backup & Export Strategy

1. **Daily Logical Export**:
   Run an automated scheduled GitHub Action or cron job executing `pg_dump` of public tables (`users`, `projects`, `project_constitutions`, `constitution_versions`, `checkpoints`, `artifacts`) to encrypted Cloudflare R2 / GCS bucket.
2. **Neon Point-in-Time Restore**:
   Neon provides an instant 6-hour point-in-time restore window on the free tier, allowing immediate rollback to any minute preceding accidental corruption or data loss.

---

## 3. Database Failover Runbook (Neon to Supabase)

If Neon experiences an extended platform outage:
1. Obtain the secondary PostgreSQL connection string from Supabase:
   ```bash
   SUPABASE_DB_URL="postgresql+asyncpg://postgres:pass@db.xyz.supabase.co:5432/postgres"
   ```
2. Run database migrations to provision the schema:
   ```bash
   DATABASE_URL="$SUPABASE_DB_URL" alembic upgrade head
   ```
3. Update the `promptiq-neon-db-url` secret in Google Secret Manager to point to Supabase:
   ```bash
   gcloud secrets versions add promptiq-neon-db-url --data-file=- <<< "$SUPABASE_DB_URL"
   ```
4. Restart Cloud Run service to bind to the new database URL:
   ```bash
   gcloud run services update promptiq-backend --region us-central1
   ```
5. Verify `/ready` returns `200 OK`.
