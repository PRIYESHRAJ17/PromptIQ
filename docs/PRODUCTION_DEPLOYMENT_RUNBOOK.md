# PROMPTIQ PRODUCTION DEPLOYMENT RUNBOOK
## Operations, Container Orchestration, Reverse Proxy & Scaling

---

## 1. Overview

This runbook specifies the step-by-step procedures for deploying, maintaining, and operating the full PromptIQ product stack in a self-hosted or cloud production environment.

---

## 2. Architecture & Components

```
[ Client Traffic (HTTPS :443) ]
               │
               ▼
   [ Caddy Reverse Proxy / TLS ]
         │               │
         │ /api/*        │ /* (Static Web UI)
         ▼               ▼
[ PromptIQ Backend ]   [ Frontend Build ]
  (FastAPI ASGI)      (React 19 / HTML)
         │
         ▼
[ PostgreSQL 16 DB ]
```

---

## 3. Deployment Options

### Option A: Docker Compose (Recommended Self-Hosted)

1. **Prerequisites**: Docker Engine 24+ and Docker Compose v2+.
2. **Build and Launch Stack**:
   ```bash
   cd deployment
   docker compose -f docker-compose.prod.yml up -d --build
   ```
3. **Verify Service Health**:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   docker compose -f docker-compose.prod.yml logs backend
   curl http://localhost/health
   ```
4. **Run Database Migrations (if applicable)**:
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

### Option B: Render Deployment (Free Tier / Cardless Cloud)

1. Connect the GitHub repository to Render.
2. In the Render Dashboard, select **New +** -> **Blueprint**.
3. Select the repository and point to `deployment/render.yaml`.
4. Render automatically provisions:
   - Web Service: `promptiq-backend` (Python 3.11, Uvicorn, health check `/health`)
   - Static Site: `promptiq-frontend` (Vite build, rewrites `/api/*` to backend)

### Option C: Fly.io Deployment

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Launch the backend:
   ```bash
   fly launch --config deployment/fly.toml --no-deploy
   fly deploy --config deployment/fly.toml
   ```

---

## 4. Environment Variables Reference

| Variable | Description | Default / Example | Mandatory |
|---|---|---|---|
| `PROMPTIQ_ENV` | Runtime environment tier | `production` | Yes |
| `PROMPTIQ_ZERO_PRICE_ENFORCEMENT` | Cryptographic rejection of paid inference & BYOK keys | `true` | Yes |
| `PROMPTIQ_DATABASE_URL` | PostgreSQL or SQLite connection string | `postgresql://...` | Yes |
| `PROMPTIQ_API_HOST` | Host binding for Uvicorn | `0.0.0.0` | Yes |
| `PROMPTIQ_API_PORT` | Port binding | `8000` | Yes |
| `VITE_PROMPTIQ_API_URL` | Frontend API target base URL | `/api/v1` | Yes |

---

## 5. Health Checks & Disaster Recovery

- **Liveness Probe**: `GET /health` -> `{"status": "healthy", "version": "4.0.0", "zero_price_policy": "enforced"}`
- **Database Backup**:
  ```bash
  docker compose -f docker-compose.prod.yml exec db pg_dump -U promptiq promptiq > backup_$(date +%Y%m%d).sql
  ```
- **Log Inspection**:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
  ```
