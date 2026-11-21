# PromptIQ Model Eligibility Registry

**Registry Revision**: 2026.11-v3.2  
**Last Verified**: November 21, 2026  
**Auditor**: Model Operations & Zero-Price Compliance Board  

---

## 1. Formal Eligibility Classification States

PromptIQ enforces nine explicit model eligibility states across all gateways and routers:

| Eligibility State | Definition & Operational Policy |
| :--- | :--- |
| **`VERIFIED_ELIGIBLE`** | Officially verified $0/token pricing, active provider free tier, verified capabilities, automated test coverage, and established terms of service. Approved for internal PromptIQ inference. |
| **`CONDITIONALLY_ELIGIBLE`** | Verified zero price, but subject to upstream community rate sharing, variable routing, or third-party uptime conditions (e.g. OpenRouter `:free` routes). Secondary failover only. |
| **`UNVERIFIED`** | Listed in external catalogs as free, but lack automated test validation, documented provider quotas, or verified stability. Prohibited from production routing. |
| **`REVIEW_REQUIRED`** | Previously eligible models undergoing provider terms of service revision, upcoming deprecation announcements, or quota restructuring. |
| **`INELIGIBLE_TERMS`** | Models whose terms of service impose commercial restrictions, user exclusivity, or redistribution prohibitions incompatible with PromptIQ. |
| **`INELIGIBLE_PRIVACY`** | Models whose providers mandate public prompt exposure, unencrypted transit, or untrusted telemetry harvesting. |
| **`INELIGIBLE_PAID`** | Commercial models requiring $/token billing or credit card funding (e.g. Claude 3.7 Sonnet, GPT-4o, Vertex AI billable endpoints). **Strictly forbidden from internal inference.** |
| **`RETIRED`** | Officially shut down, decommissioned, or deprecated models (e.g. Gemini 2.0 Flash, Gemini 1.5 Flash). Permanently blacklisted and rejected by gateway. |
| **`UNAVAILABLE`** | Routes experiencing extended infrastructure downtime, permanent 5xx responses, or unresolvable DNS failures. |

---

## 2. Active Model Pool & Eligibility Ledger

### 2.1 Verified Eligible Zero-Price Models (`VERIFIED_ELIGIBLE`)

| Model ID | Provider & Family | Context / Output | Rate Limits (RPM / RPD / TPM / TPD) | Primary Role | Verification Evidence & Terms Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`gemini-3.8-flash`** | Google (Gemini) | 1,048,576 / 8,192 | 15 RPM / 1,500 RPD / 1M TPM / 10M TPD | Orchestrator, Discovery, Synthesis | Google AI Studio Developer API free tier. Prohibits Vertex AI billable routes. [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`gemini-3.5-flash-lite`**| Google (Gemini) | 1,048,576 / 8,192 | 30 RPM / 1,500 RPD / 1M TPM / 10M TPD | Fast Model, Routine Extraction | Sub-second lightweight execution on AI Studio free tier. [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`gemini-2.5-flash`** | Google (Gemini) | 1,048,576 / 8,192 | 15 RPM / 1,500 RPD / 1M TPM / 10M TPD | Secondary Generator, Continual Turns | Stable generation route on Developer API free tier. [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`llama-3.3-70b-versatile`**| Groq (Llama) | 131,072 / 4,096 | 30 RPM / 1,000 RPD / 12k TPM / 100k TPD | Reasoning, Independent Critic | GroqCloud free tier on LPU hardware. Strict 100k TPD hard stop. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`llama-3.1-8b-instant`** | Groq (Llama) | 131,072 / 8,192 | 30 RPM / 14,400 RPD / 6k TPM / 500k TPD | Fast Burst, Classification | High-volume burst route under GroqCloud free tier. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`qwen-2.5-coder-32b`** | Groq (Qwen) | 131,072 / 4,096 | 30 RPM / 1,000 RPD / 6k TPM / 100k TPD | Coding, Syntax Verification | Specialized coding model on GroqCloud free tier. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`promptiq-mock-v1`** | Internal (Mock) | 2,000,000 / 16,384| Unlimited / Zero-Cost | Deterministic Testing, RESTRICTED Airgap | In-memory deterministic engine. Zero external egress. Safe for all classifications. |

---

### 2.2 Conditionally Eligible Zero-Price Models (`CONDITIONALLY_ELIGIBLE`)

| Model ID | Provider | Context | Limitations / Conditions | Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| `meta-llama/llama-3.3-70b-instruct:free` | OpenRouter | 131,072 | Upstream rate-sharing, variable latency | Community free tier; subject to upstream node availability. |
| `deepseek/deepseek-r1:free` | OpenRouter | 64,000 | Strict per-minute throttling | High-reasoning free route; intermittent queueing during peak hours. |
| `baidu/ernie-5.5-flash-preview:free` | OpenRouter | 32,000 | Preview terms, experimental uptime | Experimental multilingual route. |

---

### 2.3 Retired and Decommissioned Models (`RETIRED`)

| Model ID | Former Provider | Shutdown Date | Reason & Enforcement Action |
| :--- | :--- | :--- | :--- |
| **`gemini-2.0-flash`** | Google | June 1, 2026 | **Officially shut down by Google.** Hard-blocked by gateway; raises `ZeroPriceViolationError`. |
| **`gemini-2.0-flash-lite`** | Google | June 1, 2026 | **Officially shut down by Google.** Hard-blocked by gateway. |
| **`gemini-1.5-flash`** | Google | September 30, 2025 | Decommissioned legacy generation endpoint. |
| **`gemini-1.5-pro`** | Google | September 30, 2025 | Decommissioned; remaining Vertex route is billable ($/token). |
| **`text-davinci-003`** | OpenAI | January 4, 2024 | Legacy completions API shut down. |

---

### 2.4 Paid Models Prohibited from Internal Inference (`INELIGIBLE_PAID`)

| Model ID | Provider | Cost Structure | Policy & Treatment |
| :--- | :--- | :--- | :--- |
| `claude-3-7-sonnet-20250219` | Anthropic | \$3.00 / \$15.00 per MTok | **Paid Target Only.** PromptIQ compiles native instructions targeting Claude Code, but NEVER calls Anthropic APIs internally. |
| `gpt-4o` | OpenAI | \$2.50 / \$10.00 per MTok | **Paid Target Only.** Target compilation for OpenAI Codex/Cursor only. |
| `gemini-1.5-pro (Vertex AI)` | Google Cloud | \$1.25 / \$5.00 per MTok | Billable cloud endpoint. Strictly rejected by `verify_zero_price_route`. |
