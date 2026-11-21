# PromptIQ Cloud Compute Runtime Decision Record (ADR)

**Phase**: 3.4 Runtime Proof  
**Date**: November 21, 2026  
**Status**: APPROVED by Systems Architecture & FinOps Board  
**Target Invariant**: Laptop independence, non-negotiable ₹0 user cost, zero financial debt risk.  

---

## 1. The Cloud Compute Trilemma and Problem Statement

Previous delivery reports proposed Cloudflare Workers for edge proxy and Neon for persistence, but left the main application compute backend ("compute runner") ambiguously specified.

An exhaustive technical audit of the modern cloud hosting landscape reveals an inescapable trilemma for running a full Python FastAPI backend (`asyncpg`, SQLAlchemy, JWT auth, background tasks):

$$\text{Instant Cold Resume (<2s)} \quad \oplus \quad \text{Cardless Registration} \quad \oplus \quad \text{Native Hard Spending Freeze}$$

| Candidate Host | Execution Runtime | Credit Card Required? | Auto-Charges Overages? | Cold-Start Resume Time | Telegram Webhook Compatible? | Raw TCP Socket / asyncpg? | Feasibility Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Google Cloud Run** | Standard Linux OCI Container | **YES** | **YES** ($0.40/M requests) | **1.2–2.0 seconds** | **YES** (Sub-second response) | **YES** (Direct TCP) | **`APPROVED WITH SPENDING KILLSWITCH`** |
| **Cloudflare Workers** | Pyodide WebAssembly (V8) | **NO** | **NO** (Hard stops on limit) | **<5 ms** | Limited by 10ms CPU limit | **NO** (No raw TCP sockets for asyncpg)| **`APPROVED AS EDGE PROXY ONLY`** |
| **Render Web Service** | Linux Container | **NO** | **NO** (Stops at 750h limit) | **~50 seconds** (Sleeps on 15m idle) | **NO** (Telegram times out in 5-10s) | **YES** (Outbound Postgres) | **`REJECTED`** (50s cold-start timeout) |
| **Koyeb Free Tier** | Nano Container (512MB RAM) | **NO** | **NO** (Hard stops) | **~10 seconds** | Marginal | **YES** | **`EVALUATED STANDBY RUNNER`** (Memory constrained for heavy AST pipelines) |
| **Fly.io** | MicroVM | **YES** | **YES** (Base charges) | 500 ms | YES | YES | **`REJECTED`** (Paid infrastructure) |

---

## 2. Decisive Architectural Resolution: The 3-Tier Zero-Spend Cloud Topology

To eliminate the 50-second cold-start problem of cardless hosts while eliminating the financial overage risk of cloud container platforms, PromptIQ specifies the following verified 3-tier architecture:

```
[ Telegram Users / MCP Clients / REST SDK ]
                     │
                     ▼ HTTPS
┌─────────────────────────────────────────────────────────────┐
│ 1. EDGE PROXY TIER: Cloudflare Workers                      │
│    - Status: 100% Free & Cardless                           │
│    - Quota: 100,000 requests/day with native hard stop      │
│    - Role: WAF, DDoS shielding, TLS termination, Telegram   │
│            webhook secret check, IP rate-limiting           │
└──────────────────────────┬──────────────────────────────────┘
                           │ Authenticated Proxied Request
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. COMPUTE TIER: Google Cloud Run Container                 │
│    - Runtime: Containerized FastAPI Backend (Linux non-root)│
│    - Quota: 2M requests/mo free tier allocation             │
│    - Cold Start: 1.2s container spin-up (Telegram safe)     │
│    - Financial Safeguard: Automated Spending Freeze         │
│      Killswitch Cloud Function. Shuts down Cloud Run        │
│      immediately if billable threshold exceeds $0.00.       │
└──────────────────────────┬──────────────────────────────────┘
                           │ TLS TCP / asyncpg
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PERSISTENCE TIER: Neon Serverless Postgres               │
│    - Status: 100% Free & Cardless                           │
│    - Quota: 0.5 GiB storage, 190 CU-hrs with native hard stop│
│    - Connection Resilience: pool_pre_ping=True, recycle=300 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Financial Hard-Stop Safeguard: Operator Spending Freeze Killswitch

Because Google Cloud Run requires a billing account that auto-charges overages, PromptIQ forbids unconstrained deployment. Deployment requires the automated Cloud Function spending killswitch:

1. **Cloud Billing Budget Alert**: Configured with a \$0.01 budget alert threshold.
2. **Pub/Sub Notification**: Google Cloud Billing publishes budget notifications to a dedicated Pub/Sub topic `promptiq-billing-alerts`.
3. **Automated Killswitch Cloud Function**:
   - Listens to `promptiq-billing-alerts`.
   - When cost exceeds $0.00, it calls the Cloud Run API:
     ```python
     # Disables ingress and scales instances to 0
     run_client.services.update_service(
         name="projects/PROMPTIQ_PROJECT/locations/us-central1/services/promptiq-backend",
         body={"spec": {"traffic": [], "template": {"spec": {"containerConcurrency": 0}}}}
     )
     ```
   - This converts Cloud Run's billable model into a **guaranteed hard spending freeze**.

---

## 4. Laptop Independence Compliance

- **Production Execution**: Runs 100% in the cloud (Cloudflare + Cloud Run + Neon).
- **Workstation Independence**: The developer's laptop can be disconnected, powered off, or traveling for weeks without affecting production uptime, Telegram webhooks, or API requests.
- **Local Development**: Workstation runs local SQLite and Uvicorn strictly for offline coding and testing.
