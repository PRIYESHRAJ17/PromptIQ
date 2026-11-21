# Cloud Compute Decision & Hosted Runner Feasibility (Phase 3.4.2)
## Exhaustive Evaluation of Cloud Compute Runtimes for Zero-Cost Laptop-Independent Production

**Audit Date**: 2026-11-22  
**Target Workload**: PromptIQ Python Backend (FastAPI, SQLAlchemy, `asyncpg`, AST Compiler, Telegram Webhook, MCP Server)  
**Classification**: `COMPUTE_RUNNER = UNRESOLVED` / `BLOCKED_EXTERNAL` (No Fully Compliant Cardless Zero-Cost Cloud Compute Service Exists)  

---

## 1. Executive Summary

PromptIQ requires a compute runner capable of executing:
- FastAPI REST API endpoints
- Tenant authentication & Crypto Vault
- Model gateway & multi-model orchestration
- Adaptive discovery & AST compiler
- Telegram webhook listener
- Remote MCP server endpoints
- Background job processing

Prior reports suggested pairing Cloudflare Workers (as an edge proxy) with Neon Postgres. However, this leaves the core application runner missing.

An exhaustive technical evaluation of 8 hosted cloud compute providers establishes an unavoidable industry reality: **No cloud compute provider currently offers a 24/7 always-on Python ASGI runtime with raw TCP database connectivity, zero credit card requirement, and an absolute zero-spend hard stop guarantee.**

PromptIQ refuses to invent a fictional zero-cost cloud architecture. The compute runner is formally classified as **`UNRESOLVED` / `BLOCKED_EXTERNAL`**.

---

## 2. Comprehensive Provider Evaluation Matrix

| Provider & Tier | Cardless Signup? | 24/7 Always-On (No Sleeping)? | Python ASGI + `asyncpg` TCP? | Zero-Spend Hard Stop ($0.00)? | Verdict for PromptIQ |
|---|---|---|---|---|---|
| **Cloudflare Workers (Python)** | **YES** | **YES** (Sub-millisecond) | **NO** (10ms CPU limit, no raw TCP sockets for asyncpg, 25MB bundle cap) | **YES** (Hard stop at 100k req/day) | **INELIGIBLE FOR BACKEND** (Approved only as Edge Ingress/WAF). |
| **Google Cloud Run** | **NO** (Card required) | **YES** (Scale to zero with fast wake) | **YES** (Full Docker container support) | **NO** (Billing latency gap of hours; charges can accrue) | **REJECTED** (Fails cardless zero-exposure invariant). |
| **Render.com (Free Tier)** | **YES** | **NO** (Sleeps after 15m; 50s cold start breaks Telegram) | **YES** (Standard Linux container) | **YES** (Hard limit at 750 hours/month) | **INELIGIBLE FOR TELEGRAM** (50s cold start causes webhook timeouts). |
| **Fly.io** | **NO** (Card required) | **YES** (Can scale to zero) | **YES** (Docker container support) | **NO** (Card charged for overages) | **REJECTED** (Card required). |
| **Railway** | **NO** (Paid only) | N/A | **YES** | **NO** (No free tier) | **REJECTED** (Paid service only). |
| **Hugging Face Spaces (Docker)**| **YES** | **NO** (Sleeps after 48h; public by default) | **YES** (2 vCPU / 16 GB RAM Docker) | **YES** (Free tier cannot bill) | **CONDITIONAL** (Suitable for public demo, but public visibility issues). |
| **Koyeb (Free Tier)** | **NO** (Card required) | **NO** (1 nano instance, sleeps) | **YES** | **NO** (Card required) | **REJECTED** (Card required). |
| **Oracle Cloud Always Free** | **NO** (Card required) | **YES** (4 ARM OCPU / 24 GB) | **YES** | **YES** (Always Free tier) | **REJECTED** (Strict credit card verification). |

---

## 3. The Cold-Start & Webhook Trilemma

1. **Telegram Webhook Constraint**:
   - The Telegram Bot API enforces a **5-second timeout** when delivering webhook updates. If the server does not respond with HTTP 200 within 5 seconds, Telegram retries and eventually suspends the webhook.
   - Free services that sleep (like Render.com with a 50-second wake-up time) **fail 100% of incoming Telegram messages** after 15 minutes of inactivity.
2. **Database Connection Constraint**:
   - Standard PostgreSQL drivers (`asyncpg`, `psycopg3`) require raw TCP sockets.
   - Serverless platforms running inside browser-style WebAssembly runtimes (Cloudflare Workers) do not support raw TCP sockets on free tiers, requiring HTTP-based proxies or custom WebSockets that break standard SQLAlchemy engines.
3. **Cardless Requirement vs. Cloud Fraud Prevention**:
   - Cloud providers have almost universally eliminated cardless always-on compute to prevent crypto-mining and botnet abuse.

---

## 4. Legitimate Paths Forward for PromptIQ

Because no hosted provider satisfies all constraints simultaneously, PromptIQ defines two explicit, transparent deployment tracks:

### Track A: Local Operator Staging (Zero-Spend, Cardless, 100% Laptop-Dependent)
- The backend runs locally on the operator's machine during active development and evaluation sessions.
- Suitable for code development, automated testing, and synthetic prompt engineering.
- **Limitation**: Violates laptop independence. Cannot serve production users 24/7.

### Track B: Operator-Authorized Cloud Deployment (Laptop-Independent, Low Financial Exposure)
- The operator consciously chooses to supply a credit card to **Google Cloud Run** or **Render**, accepting the minor risk of billing latency in exchange for a 24/7 live service.
- PromptIQ configures container limits:
  - Cloud Run max instances: `1`
  - Concurrency: `80`
  - CPU: `1 vCPU`, Memory: `512 MiB`
  - Monthly budget alert set at `$1.00`.
- **Status**: Requires explicit, uncoerced operator approval. PromptIQ will never automatically provision or configure this track.
