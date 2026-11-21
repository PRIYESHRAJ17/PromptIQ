# PromptIQ Cloud Production Deployment Guide

This guide walks an operator through deploying the PromptIQ product foundation to zero-cost cloud-native infrastructure (Google Cloud Run + Neon Serverless Postgres), completely freeing production operation from the user's workstation.

---

## Prerequisites

1. **Google Cloud Account** (Free tier with $0 recurring spend).
2. **Neon.tech Account** (Free serverless Postgres tier: 1 GB storage, no credit card required).
3. **Google Cloud SDK (`gcloud`)** installed on the workstation.
4. **Docker** installed on the workstation (or built via Cloud Build).

---

## Step 1: Provision Persistent Cloud Database (Neon Postgres)

1. Log in to [Neon.tech](https://neon.tech) and create a project named `promptiq-prod`.
2. Select PostgreSQL version 16 and your preferred region (e.g., `us-east-1` or `us-central-1`).
3. Copy the pooled connection string:
   ```
   postgresql://user:password@ep-xyz-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. For SQLAlchemy async execution, replace the scheme with `postgresql+asyncpg://`:
   ```
   postgresql+asyncpg://user:password@ep-xyz-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

---

## Step 2: Configure Operator Cloud Secrets (Google Secret Manager)

Store operator-managed credentials securely in Google Cloud Secret Manager so no secrets ever appear in Git or configuration files:

```bash
# 1. JWT Encryption Secret Key (Minimum 32 random characters)
gcloud secrets create promptiq-jwt-secret --data-file=- <<< "$(openssl rand -base64 32)"

# 2. Neon Database URL
gcloud secrets create promptiq-neon-db-url --data-file=- <<< "postgresql+asyncpg://user:password@ep-xyz-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# 3. Google Gemini Developer API Key (Free tier server-side key)
gcloud secrets create promptiq-gemini-key --data-file=- <<< "YOUR_OPERATOR_GEMINI_API_KEY"

# 4. GroqCloud API Key (Secondary free tier key)
gcloud secrets create promptiq-groq-key --data-file=- <<< "YOUR_OPERATOR_GROQ_API_KEY"

# 5. Telegram Bot Token & Webhook Secret
gcloud secrets create promptiq-telegram-token --data-file=- <<< "YOUR_TELEGRAM_BOT_TOKEN"
gcloud secrets create promptiq-telegram-webhook-secret --data-file=- <<< "$(openssl rand -hex 24)"
```

---

## Step 3: Run Database Migrations in the Cloud

Before routing public traffic, run the initial Alembic schema migrations against the cloud database:

```bash
DATABASE_URL="postgresql+asyncpg://user:password@ep-xyz-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```
This generates all 22 relational tables, constraints, and indices in Neon Postgres.

---

## Step 4: Build and Deploy to Google Cloud Run

### Option A: Using Google Cloud Build & Cloud Run CLI
```bash
# Build container image in Google Cloud Build
gcloud builds submit --tag gcr.io/$GCP_PROJECT/promptiq-backend:latest -f deployment/docker/Dockerfile .

# Deploy container to Cloud Run with scale-to-zero enabled (₹0 idle cost)
gcloud run deploy promptiq-backend \
  --image gcr.io/$GCP_PROJECT/promptiq-backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars PROMPTIQ_ENV=production,PROMPTIQ_LOG_LEVEL=INFO,ENFORCE_ZERO_PRICE_ONLY=true,MANAGED_INFERENCE_PRIMARY_ROUTE=gemini \
  --set-secrets PROMPTIQ_SECRET_KEY=promptiq-jwt-secret:latest,DATABASE_URL=promptiq-neon-db-url:latest,OPERATOR_GEMINI_API_KEY=promptiq-gemini-key:latest,OPERATOR_GROQ_API_KEY=promptiq-groq-key:latest,TELEGRAM_BOT_TOKEN=promptiq-telegram-token:latest,TELEGRAM_WEBHOOK_SECRET=promptiq-telegram-webhook-secret:latest
```

### Option B: Using Terraform
```bash
cd deployment/terraform
terraform init
terraform apply -var="gcp_project_id=$GCP_PROJECT" -var="container_image=gcr.io/$GCP_PROJECT/promptiq-backend:latest"
```

---

## Step 5: Register Telegram Bot Webhook

After Cloud Run deployment completes, register the public HTTPS webhook URL with the official Telegram Bot API:

```bash
SERVICE_URL=$(gcloud run services describe promptiq-backend --platform managed --region us-central1 --format 'value(status.url)')
WEBHOOK_SECRET=$(gcloud secrets versions access latest --secret=promptiq-telegram-webhook-secret)
BOT_TOKEN=$(gcloud secrets versions access latest --secret=promptiq-telegram-token)

curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${SERVICE_URL}/api/v1/telegram/webhook\", \"secret_token\": \"${WEBHOOK_SECRET}\"}"
```

---

## Step 6: Connect Remote MCP Clients

For external AI agents (such as Cursor, Claude Desktop, or Google Antigravity) running on local workstations, configure the remote bridge in `mcp_config.json`:

```json
{
  "mcpServers": {
    "promptiq": {
      "command": "python",
      "args": [
        "-m",
        "promptiq.mcp.client_bridge",
        "--url",
        "https://promptiq-backend-xyz.a.run.app/api/v1/mcp/rpc",
        "--token",
        "YOUR_USER_ACCESS_TOKEN"
      ]
    }
  }
}
```

---

## Step 7: Mandatory Laptop-Independence Acceptance Test

1. Obtain the public service URL: `https://promptiq-backend-xyz.a.run.app`.
2. Confirm health probe: `curl https://promptiq-backend-xyz.a.run.app/health`.
3. Create a test project through the public API using curl or Postman.
4. **SHUT DOWN OR DISCONNECT THE DEVELOPMENT LAPTOP**.
5. From an external device (e.g. mobile phone via Telegram or separate computer):
   - Send `/start` or `/projects` to the Telegram bot.
   - Verify that the bot responds immediately.
   - Run a prompt autopsy or project discovery turn.
   - Confirm project records persist across container recycles.
6. Record completion: **"LAPTOP-INDEPENDENCE VERIFIED."**
