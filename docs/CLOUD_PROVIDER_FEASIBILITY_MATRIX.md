# PromptIQ Cloud Provider Feasibility Matrix
## Exhaustive Infrastructure Analysis for 100% Free, Laptop-Independent Deployment

**Revision**: 2026.11-v3.3  
**Date**: November 21, 2026  
**Auditor**: Cloud Infrastructure & FinOps Engineering Group  
**Core Invariant**: Laptop independence, 100% free operation ($0.00 / ₹0), native hard stops, zero credit card debt risk.

---

## 1. Cloud Infrastructure Providers Evaluation Matrix

| # | Provider & Service | Free Tier Resource Allowance | Credit Card Required? | Overage Hard Stop? | Inactivity Pausing / Sleep? | Technical Feasibility for PromptIQ Backend | Approval Status & Role |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | **Cloudflare Workers** | 100,000 requests/day, 10ms CPU/req | **No** | **Yes** (Native hard stop) | None (Always active at edge) | Python Workers run on V8 WebAssembly (Pyodide); cannot open raw TCP sockets for asyncpg without Hyperdrive. Fast for edge routing. | **`APPROVED`** (Edge Proxy, WAF, Rate Limiting, TLS Ingress) |
| 2 | **Neon Serverless Postgres** | 0.5 GiB storage, 190 Compute Unit-hours/mo | **No** | **Yes** (Connections refused at limit) | Auto-suspends idle compute (resumes in ~500ms via connection proxy) | Fully standard PostgreSQL 16+. Compatible with asyncpg, SQLAlchemy, Alembic. Requires `pool_pre_ping=True`. | **`APPROVED`** (Primary Production Database) |
| 3 | **Cloudflare D1** | 5M reads/day, 100k writes/day, 5GB storage | **No** | **Yes** (Hard stops on free plan) | None (Edge database) | SQLite-compatible edge DB. Does not support asyncpg/Postgres wire protocol. Requires complete ORM driver rewrite. | **`CONDITIONALLY_FEASIBLE`** (Secondary Edge Cache) |
| 4 | **Turso (libSQL)** | 9GB storage, 1B row reads/mo, 25M writes/mo | **No** | **Yes** (Hard stops on free tier) | None | Embedded SQLite/libSQL via HTTP. Requires database adapter refactoring from asyncpg/Postgres. | **`FEASIBLE_ALTERNATIVE`** (Alternative SQLite backend) |
| 5 | **Supabase** | 500MB database, 2 projects | **No** | **Yes** | **YES: Pauses after 7 days of inactivity** | Standard Postgres, but weekly auto-pausing violates 24/7 laptop-independent availability. | **`REJECTED`** (Weekly inactivity pausing) |
| 6 | **Google Cloud Run** | 2M requests/mo, 360k GB-sec, 180k vCPU-sec | **Yes** (Billing account) | **NO: Auto-charges credit card** | Scales to zero (fast cold start ~1-2s) | Complete Linux container execution. Runs FastAPI/Uvicorn natively. However, lacks native hard spending caps. | **`REJECTED_CREDIT_CARD_OVERAGE`** (Financial debt risk) |
| 7 | **AWS Lambda** | 1M requests/mo, 3.2M sec compute | **Yes** (Credit card) | **NO: Auto-charges credit card** | Cold starts | Requires Mangum adapter. Lacks native hard spending caps. | **`REJECTED_CREDIT_CARD_OVERAGE`** (Financial debt risk) |
| 8 | **Microsoft Azure Functions** | 1M executions/mo | **Yes** (Credit card) | **NO: Auto-charges credit card** | Cold starts | Lacks native hard spending caps. | **`REJECTED_CREDIT_CARD_OVERAGE`** (Financial debt risk) |
| 9 | **Render Free Web Service** | 750 hours/mo, 512MB RAM | **No** | **Yes** (Stops at 750h) | **YES: Sleeps after 15 min idle; 50s cold start** | Ephemeral file system, severe 50-second spin-up time triggers Telegram webhook timeouts. | **`REJECTED`** (Unusable 50s cold start) |
| 10 | **Fly.io** | No longer has free tier | **Yes** | Paid | N/A | Hobby plan requires payment method and charges minimum base fees. | **`REJECTED`** (Paid infrastructure) |
| 11 | **Koyeb** | 1 web service, 512MB RAM | **No** | **Yes** (Hard stop) | Sleeps when idle | Micro-container instance. Limited CPU capacity. | **`EVALUATED_STANDBY`** (Secondary failover runner) |

---

## 2. Deep Dive on Architectural Feasibility

### 2.1 The Database Tier: Neon Serverless Postgres
- **Why Neon Won**:
  1. True cardless registration ($0 forever without entering billing details).
  2. Native hard stop: When 190 CU-hours or 0.5 GiB is reached, Neon cleanly refuses new connections (`Active branches limit reached`), completely preventing financial surprises.
  3. Wire-compatible PostgreSQL: PromptIQ uses SQLAlchemy 2.0 with `asyncpg`. Neon supports full SQL semantics, migrations via Alembic, constraints, and JSONB.
- **Handling Serverless Cold Resumes**:
  Neon scales compute to zero when idle. To prevent stale connection errors when compute wakes up:
  ```python
  engine = create_async_engine(
      DATABASE_URL,
      pool_pre_ping=True,      # Tests connection liveness before checkout
      pool_recycle=300,        # Recycles connections every 5 minutes
      pool_size=5,             # Conserves serverless connection slots
      max_overflow=10,
  )
  ```

### 2.2 The Ingress Tier: Cloudflare Workers
- **Why Cloudflare Edge Ingress Won**:
  1. 100,000 requests/day free with native hard stop on free plans.
  2. Protects backend from DDoS, performs TLS termination, and validates Telegram webhook secret tokens at the edge.
  3. Zero cold starts (executes in <5ms across 300+ global data centers).

### 2.3 The Compute Tier Bottleneck
- **The Core Cloud Dilemma**:
  - Services with complete cardless free tiers (Render, Koyeb) impose aggressive idle sleeps (15-50s cold starts) that break Telegram webhooks (Telegram times out after 5-10s).
  - Services with instantaneous container execution (Google Cloud Run, AWS Lambda) mandate a credit card on file and automatically bill overages rather than hard-stopping.
  - Cloudflare Python Workers execute in WebAssembly Pyodide and cannot run raw asyncpg TCP sockets without proprietary bridges.
- **FinOps Verdict**: PromptIQ must adopt **Outcome B** (hybrid architecture) where edge and database are fully verified zero-spend, and compute execution strategy is explicitly governed to prevent unapproved billing.
