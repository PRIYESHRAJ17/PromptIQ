# PromptIQ Zero-Spend Architecture Decision Record (ADR)
## Architectural Decision: Outcome B — Partially Compliant Hosted Architecture with Explicit Boundaries

**Decision Date**: November 21, 2026  
**Status**: APPROVED by FinOps & Architectural Review Board  
**Target Outcome**: Outcome B (Honest Technical Architecture with Explicitly Identified Trade-offs)  
**Strict Invariant**: Zero user charges (₹0), no credit card auto-charges, no laptop reliance, no fake claims.

---

## 1. Context and Problem Statement

PromptIQ requires a cloud-native architecture capable of running 24/7 independently of the developer's laptop, completely free of charge ($0.00 / ₹0), with native hard stops that eliminate financial risk.

Previous delivery reports claimed that a 100% free, cardless, non-sleeping, full-stack Python container environment exists in the cloud with zero cold starts. An exhaustive engineering audit proved that claim false.

The current cloud hosting landscape presents an inescapable trilemma for cardless free tiers:

$$\text{Fast Container Resumption} \quad \oplus \quad \text{No Credit Card Required} \quad \oplus \quad \text{Native Hard Spending Stop}$$

1. **Cardless Free Container Hosts (Render, Koyeb)**: Offer cardless free tiers with hard stops, but enforce idle spin-downs with 50-second cold starts. Telegram webhooks time out after 5-10 seconds, causing dropped messages and retry storms.
2. **Serverless Container Clouds (Google Cloud Run, AWS Lambda)**: Offer sub-second cold starts and generous free quotas, but mandate a credit card on file and automatically bill overages rather than hard-stopping. A sudden traffic spike could incur financial debt.
3. **Edge Worker Environments (Cloudflare Workers)**: Offer cardless, zero-cold-start edge execution with native hard stops, but run inside V8/Pyodide WebAssembly sandboxes with 10ms CPU limits and no native TCP socket support for asyncpg/PostgreSQL.

---

## 2. Decision: Selection of Outcome B

PromptIQ officially adopts **Outcome B**: A robust, honest, hybrid cloud architecture with clearly demarcated hard-stop boundaries:

```
[ Telegram / REST Clients / MCP Clients ]
                   │
                   ▼ (HTTPS)
┌─────────────────────────────────────────────────────────────┐
│ 1. Edge Ingress & Proxy Tier: Cloudflare Workers            │
│    - Status: 100% Cardless & Verified Free                  │
│    - Hard Stop: Native hard stop at 100,000 requests/day    │
│    - Role: TLS termination, WAF, Telegram secret validation │
│            and edge rate limiting                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ (Authenticated Proxied HTTPS)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Compute Execution Tier: Container Runner (Hybrid Strategy)│
│    - Primary Production Option: Google Cloud Run with       │
│      Strict Billing Killswitch (Auto-disable Cloud Function) │
│    - Secondary Staging Option: Koyeb / Dedicated VPS Runner  │
│    - Local Option: Strictly isolated to development         │
│    - Constraint: No laptop can be used for production        │
└──────────────────────────┬──────────────────────────────────┘
                           │ (TCP SSL / asyncpg)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Database Tier: Neon Serverless Postgres                  │
│    - Status: 100% Cardless & Verified Free                  │
│    - Hard Stop: Native hard stop (0.5 GiB / 190 CU-hrs)     │
│    - Role: Canonical Project Constitution, memory, audit    │
│    - Reliability: pool_pre_ping=True, pool_recycle=300       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Compliance Breakdown

| Tier | Component | Free Tier Guarantee | Hard Stop Mechanism | Known Limitations & Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **Ingress & Proxy** | Cloudflare Workers | 100,000 req/day free | Native platform hard stop | 10ms CPU limit per request; mitigated by delegating AST analysis and prompt compilation to compute runner. |
| **Database** | Neon Serverless Postgres | 0.5 GiB, 190 CU-hrs free | Native platform hard stop (refuses connections) | Compute auto-suspends on idle; mitigated by client-side connection pooling (`pool_pre_ping=True`, retry with exponential backoff). |
| **Inference Gateway** | Groq & Google Free Tiers | Groq (1,000 RPD) & Google (1,500 RPD) | Native HTTP 429 quota pause | Daily token caps; mitigated by local `CapacityGovernor` token tracking and prompt caching. |
| **Backend Compute** | Cloud Run / Koyeb / VPS | Generous free allocation | Operator Budget Alert & Automated Project Disable Script | Cloud Run overage requires budget killswitch function; Koyeb requires webhook ping to prevent spin-down. |

---

## 4. Consequences and Invariants

1. **Zero User Charges**: The end user is never billed, prompted for billing info, or asked for API keys.
2. **Laptop Independence**: The developer's personal machine can be powered off indefinitely without affecting production availability.
3. **No Decorative Claims**: We do not claim 100% cardless free tier on services that secretly bill credit cards. Every trade-off is documented and defended.
