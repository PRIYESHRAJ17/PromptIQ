# PromptIQ Cloud Cost and Capacity Analysis

**Objective**: Deliver a resilient, scalable, always-available cloud intelligence backend with **₹0 / $0.00 recurring operating cost** and zero user charges.

---

## 1. Zero-Cost Infrastructure Budget Breakdown

| Service Component | Cloud Provider | Free Tier Allocation | Estimated PromptIQ Consumption | Monthly Cost | Hard Spending Boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API Compute & Ingress** | Google Cloud Run | 2,000,000 requests/mo<br>360,000 GiB-sec memory<br>180,000 vCPU-sec compute | ~50,000 requests/mo<br>~15,000 vCPU-sec<br>~30,000 GiB-sec | **$0.00** (₹0) | Billing budget set to $0.01; automated alert and scale cap. |
| **Relational Database** | Neon Serverless Postgres | 1 GB persistent storage<br>100 CU-hours compute/mo<br>Autosuspends after 5 min idle | ~150 MB database storage<br>~25 CU-hours compute | **$0.00** (₹0) | No credit card required. Auto-suspends compute when idle. |
| **Cloud Object Storage** | Cloudflare R2 / GCS | 10 GB free storage<br>Zero egress fees (R2) | ~1 GB stored artifacts & exports | **$0.00** (₹0) | Storage capped at free allotment. |
| **Primary Model Inference** | Google AI Studio | 15 RPM / 1,000,000 TPM<br>1,500 Requests/day | Variable developer usage | **$0.00** (₹0) | Free tier rate cards strictly enforced ($0/token). |
| **Secondary Inference** | GroqCloud | 30 RPM / 1,000 RPD<br>100,000 Tokens/day | Burst / Autopsy fallback | **$0.00** (₹0) | Free tier rate limit (HTTP 429 fail-closed). |
| **Telegram Bot Host** | Telegram Cloud | Free Bot API webhooks | Unlimited webhook traffic | **$0.00** (₹0) | Standard Telegram Bot API terms. |
| **Total Monthly Spend** | — | — | — | **₹0.00** | **Guaranteed Free** |

---

## 2. Capacity Model & Throughput Ceilings

Under the ₹0 cost profile, PromptIQ can sustainably support the following daily operational capacity:

1. **Daily Active Projects**: Up to 1,500 interactive project discovery turns per day.
2. **Concurrent Invocations**: 10 simultaneous user requests (enforced via `CapacityGovernor.concurrency_semaphore`).
3. **Prompt Autopsy Throughput**: Up to 1,000 prompt diagnostic runs per day using Groq / Gemini burst tiers.
4. **Database Scalability**: 1 GB of storage in Neon Postgres supports approximately 25,000 distinct Project Constitutions and versioned snapshots.
5. **Cold-Start Response**:
   - Cloud Run container cold start: ~1.2 seconds.
   - Neon Postgres compute cold start: ~400 milliseconds.
   - Warm latency: < 50 milliseconds (FastAPI response).

---

## 3. Financial Safety & Zero-Overage Guarantees

1. **Hard Billing Caps**: Cloud billing accounts must be configured with a budget of $0.01 and automated action to stop services if any unexpected paid usage is incurred.
2. **Zero Paid Routes**: Any route configured with non-zero input or output pricing is rejected by the gateway before dispatch.
3. **No BYOK**: Rejection of user-supplied API keys guarantees users can never be billed directly or indirectly.
