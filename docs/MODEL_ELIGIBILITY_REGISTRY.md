# PromptIQ Model Eligibility Registry

**Registry Revision**: 2026.11-v3.3 (Phase 3.3 Production Feasibility Release)  
**Last Verified**: November 21, 2026  
**Auditor**: Model Operations & Zero-Price Compliance Board  

---

## 1. Formal Eligibility Classification States

PromptIQ enforces eleven explicit model eligibility states across all gateways, routers, and orchestrators:

| Eligibility State | Definition & Operational Policy |
| :--- | :--- |
| **`VERIFIED_ELIGIBLE`** | Officially verified $0/token pricing, active provider free tier, verified capabilities, automated test coverage, and established terms of service. Approved for internal PromptIQ inference. |
| **`CONDITIONALLY_ELIGIBLE`** | Verified zero price, but subject to upstream community rate sharing, neuron daily limits, variable routing, or third-party uptime conditions (e.g. OpenRouter `:free` routes, Cloudflare Workers AI free tier). Secondary failover / auxiliary classifier only. |
| **`UNVERIFIED`** | Listed in external catalogs as free, but lack automated test validation, documented provider quotas, or verified stability. Prohibited from production routing. |
| **`REVIEW_REQUIRED`** | Previously eligible models undergoing provider terms of service revision, upcoming deprecation announcements, or quota restructuring. |
| **`INELIGIBLE_TERMS`** | Models whose terms of service impose commercial restrictions, user exclusivity, evaluation-only non-commercial clauses (e.g. NVIDIA NIM, Mistral MNPL, Cohere Trial), or severe unusable rate throttling (e.g. SambaNova cardless 20 RPD). |
| **`INELIGIBLE_PRIVACY`** | Models whose providers mandate public prompt exposure, unencrypted transit, or untrusted telemetry harvesting. |
| **`INELIGIBLE_PAID`** | Commercial models requiring $/token billing, upfront cash deposits, or subscriptions (e.g. Claude 3.7 Sonnet, GPT-4o, Vertex AI billable endpoints, Together AI, DeepInfra). **Strictly forbidden from internal inference.** |
| **`INELIGIBLE_BILLING`** | Services that offer temporary promotional trial credits (e.g. Cerebras $5 30-day credit) but require a credit card on file and automatically convert to paid pay-as-you-go billing upon credit expiry or exhaustion. Strictly rejected. |
| **`INELIGIBLE_AUDIENCE`** | Models whose terms forbid the application's target audience (e.g. Google Gemini Developer API terms strictly prohibit applications directed towards or accessed by individuals under 18 years old). |
| **`RETIRED`** | Officially shut down, decommissioned, or deprecated models (e.g. Gemini 2.0 Flash, Gemini 1.5 Flash, Groq legacy llama-3.3-70b-versatile). Permanently blacklisted and rejected by gateway. |
| **`UNAVAILABLE`** | Routes experiencing extended infrastructure downtime, permanent 5xx responses, or unresolvable DNS failures. |

---

## 2. Active Model Pool & Eligibility Ledger

### 2.1 Verified Eligible Zero-Price Models (`VERIFIED_ELIGIBLE`)

| Model ID | Provider & Family | Context / Output | Rate Limits (RPM / RPD / TPM / TPD) | Primary Role | Verification Evidence & Terms Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`gemini-3.8-flash`** | Google (Gemini) | 1,048,576 / 8,192 | 15 RPM / 1,500 RPD / 1M TPM / 10M TPD | Orchestrator, Discovery, Synthesis | Google AI Studio Developer API free tier. No credit card required. Prohibits Vertex AI billable routes. Data subject to human review; adult audience only (18+). [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`gemini-3.5-flash-lite`**| Google (Gemini) | 1,048,576 / 8,192 | 30 RPM / 1,500 RPD / 1M TPM / 10M TPD | Fast Model, Routine Extraction | Sub-second lightweight execution on AI Studio free tier. [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`gemini-2.5-flash`** | Google (Gemini) | 1,048,576 / 8,192 | 15 RPM / 1,500 RPD / 1M TPM / 10M TPD | Secondary Generator, Continual Turns | Stable generation route on Developer API free tier. [Pricing Docs](https://ai.google.dev/gemini-api/docs/pricing) |
| **`openai/gpt-oss-120b`** | Groq (gpt-oss) | 131,072 / 4,096 | 30 RPM / 1,000 RPD / 8k TPM / 100k TPD | Reasoning, Independent Critic | Active open-weight candidate on GroqCloud free tier. No card required. Zero training on user data. Strict 100k TPD ceiling. Paid Developer Plan excluded. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`openai/gpt-oss-20b`** | Groq (gpt-oss) | 131,072 / 8,192 | 30 RPM / 14,400 RPD / 6k TPM / 500k TPD | Fast Burst, Classification | High-volume burst route under GroqCloud free tier. 14,400 RPD. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`qwen/qwen3.8-27b`** | Groq (Qwen) | 131,072 / 4,096 | 30 RPM / 1,000 RPD / 6k TPM / 100k TPD | Coding, Syntax Verification | Specialized coding model on GroqCloud free tier, superseding legacy 2.5/3.6. [Groq Limits](https://console.groq.com/docs/rate-limits) |
| **`promptiq-mock-v1`** | Internal (Mock) | 2,000,000 / 16,384| Unlimited / Zero-Cost | Deterministic Testing, RESTRICTED Airgap | In-memory deterministic engine. Zero external egress. Safe for all classifications. |

---

### 2.2 Conditionally Eligible Zero-Price Models (`CONDITIONALLY_ELIGIBLE`)

| Model ID | Provider | Context | Limitations / Conditions | Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`@cf/meta/llama-3.1-8b-instruct`** | Cloudflare Workers AI | 131,072 | 10,000 Neurons/day free allowance (~200k tokens), hard stop on free plans | Verified $0 on Cloudflare free plan. Native hard stop prevents overage billing. Lightweight fast model / classifier role only. [Cloudflare Docs](https://developers.cloudflare.com/workers-ai/platform/pricing/) |
| **`meta-llama/llama-3.3-70b-instruct:free`** | OpenRouter | 131,072 | Strict 50 RPD limit for cardless accounts (<$10 lifetime purchases), upstream variable rate-sharing | Community free tier; subject to upstream node availability and severe 50 RPD account ceiling. [OpenRouter Docs](https://openrouter.ai/docs/limits) |
| **`deepseek/deepseek-r1:free`** | OpenRouter | 64,000 | 50 RPD limit, strict per-minute community queueing | High-reasoning free route; intermittent queueing during peak hours. |
| **`baidu/ernie-5.5-flash-preview:free`** | OpenRouter | 32,000 | 50 RPD limit, preview terms, experimental uptime | Experimental multilingual route. |

---

### 2.3 Evaluated Ineligible Providers & Candidates

| Provider & Candidate | State | Primary Failure Gate | Reason & Regulatory / Terms Evidence |
| :--- | :--- | :--- | :--- |
| **Cerebras** (`llama-3.3-70b`) | `INELIGIBLE_BILLING` | Gate B (No Free Tier) & Gate E (Credit Card) | No permanent free tier. Promotional $5 trial credit expires in 30 days and mandates a verified credit card. Converts automatically to paid pay-as-you-go billing. |
| **SambaNova** (`Meta-Llama-3.3-70B-Instruct`) | `INELIGIBLE_TERMS` | Gate C (Production Viability) & Gate E (Credit Card) | Cardless free tier is throttled to an unusable 20 Requests Per Day (RPD). Adding a credit card activates Developer tier with paid $/token billing. |
| **NVIDIA NIM** (`build.nvidia.com`) | `INELIGIBLE_TERMS` | Gate D (Commercial / Production Terms) | Free developer endpoints are strictly restricted to personal development, research, and evaluation. Commercial production mandates NVIDIA AI Enterprise license ($4,500/GPU/yr). |
| **Mistral AI** (`codestral-2501`) | `INELIGIBLE_TERMS` | Gate D (Commercial Terms) | Free access is governed by the Mistral Non-Production License (MNPL), which explicitly forbids production user interactions. Production API routes bill per token. |
| **Cohere** (`command-r-plus`) | `INELIGIBLE_TERMS` | Gate D (Commercial Terms) | Trial API keys are restricted to non-production evaluation and hard-capped at 1,000 calls/month. Commercial production requires credit card pay-as-you-go. |
| **Together AI** | `INELIGIBLE_PAID` | Gate B (No Free Tier) | No free tier exists. Requires a minimum upfront prepaid deposit of $15. |
| **DeepInfra** | `INELIGIBLE_PAID` | Gate B (No Free Tier) | Promotional $5 credit only, requires a $10 credit card deposit for production usage. |
| **Hugging Face Inference Providers** | `INELIGIBLE_PAID` | Gate B (No Free Tier) | Free tier provides a negligible allowance (~$0.10/mo), requiring a PRO subscription ($9/mo) or payment method for volume. |

---

### 2.4 Retired and Decommissioned Models (`RETIRED`)

| Model ID | Former Provider | Shutdown Date | Reason & Enforcement Action |
| :--- | :--- | :--- | :--- |
| **`gemini-2.0-flash`** | Google | June 1, 2026 | **Officially shut down by Google.** Hard-blocked by gateway; raises `ZeroPriceViolationError`. |
| **`gemini-2.0-flash-lite`** | Google | June 1, 2026 | **Officially shut down by Google.** Hard-blocked by gateway. |
| **`gemini-1.5-flash`** | Google | September 30, 2025 | Decommissioned legacy generation endpoint. |
| **`gemini-1.5-pro`** | Google | September 30, 2025 | Decommissioned; remaining Vertex route is billable ($/token). |
| **`llama-3.3-70b-versatile`** | Groq | October 31, 2026 | **Retired on GroqCloud endpoints.** Hard-blocked by gateway. |
| **`llama-3.1-8b-instant`** | Groq | October 31, 2026 | **Retired on GroqCloud endpoints.** Hard-blocked by gateway. |
| **`qwen-2.5-coder-32b`** | Groq | October 31, 2026 | **Retired on GroqCloud endpoints.** Hard-blocked by gateway. |
| **`text-davinci-003`** | OpenAI | January 4, 2024 | Legacy completions API shut down. |

---

### 2.5 Paid Models Prohibited from Internal Inference (`INELIGIBLE_PAID`)

| Model ID | Provider | Cost Structure | Policy & Treatment |
| :--- | :--- | :--- | :--- |
| `claude-3-7-sonnet-20250219` | Anthropic | \$3.00 / \$15.00 per MTok | **Paid Target Only.** PromptIQ compiles native instructions targeting Claude Code, but NEVER calls Anthropic APIs internally. |
| `gpt-4o` | OpenAI | \$2.50 / \$10.00 per MTok | **Paid Target Only.** Target compilation for OpenAI Codex/Cursor only. |
| `gemini-1.5-pro (Vertex AI)` | Google Cloud | \$1.25 / \$5.00 per MTok | Billable cloud endpoint. Strictly rejected by `verify_zero_price_route`. |
