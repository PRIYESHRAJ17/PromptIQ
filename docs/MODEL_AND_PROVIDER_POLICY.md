# PromptIQ Model and Provider Governance Policy

## 1. Core Operating Principles

1. **User Cost is Always ₹0**: No user-facing charges, no credit cards, no subscriptions, no token meters.
2. **Strictly No BYOK (Bring Your Own Key)**: PromptIQ never asks users to supply OpenAI, Anthropic, Gemini, Groq, or OpenRouter API keys.
3. **No Local Model Prerequisite**: Official PromptIQ is a centrally hosted cloud service. Users are never required to run local LLMs or provide GPU compute.
4. **Separation of Internal Engine vs. Target Model**:
   - **Internal Model**: The centrally curated, zero-price hosted LLM powering PromptIQ's discovery, autopsy, research synthesis, and compilation. Centrally managed; users do not configure or see a model picker for internal operations.
   - **Target Model**: The destination model for which PromptIQ compiles native instruction packages (e.g., Claude 3.7 Sonnet, GPT-4o, Gemini 2.0 Flash, DeepSeek R1). Users freely select or receive recommendations for their target environment.

---

## 2. Hard Provider Eligibility Gate

Any candidate model route proposed for PromptIQ's internal intelligence engine must pass all five mandatory eligibility gates:

| Gate | Requirement | Verification Method |
| :--- | :--- | :--- |
| **Gate 1: Zero-Price Route** | Must have documented $0 cost for input and output tokens under the operating tier. Any route with billable risk is rejected. | Pricing documentation audit & automated hard check in API adapter. |
| **Gate 2: Hosted Multi-User Terms** | Provider Terms of Service must permit hosted application routing without violating user quotas or terms. | Terms of Service legal review. |
| **Gate 3: Privacy & Data Use** | Data retention and training policies must be documented. Sensitive project context must not be routed to unconsented public training pipelines. | Provider privacy policy check and transparent user disclosures. |
| **Gate 4: Architectural Capabilities** | Must reliably support structured outputs (JSON schema), tool calling, minimum 32k context window, and high-fidelity instruction following. | Benchmark evaluation using PromptIQ validation test suite. |
| **Gate 5: Operational Stability** | Documented rate limits, predictable latency, and active API availability. | Capacity Governor tracking and circuit breaker monitoring. |

---

## 3. Evaluation of Candidate Zero-Price Routes

| Provider Route | Model Identifier | Documented Free Quotas | Privacy / Data Terms | Current Status in PromptIQ |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini Developer API** | `gemini-1.5-flash` / `gemini-2.0-flash` | Free tier input/output with rate limits (RPM/RPD). | Free tier content may be used to improve Google products; transparent disclosure required. | **Primary Candidate** for fast, high-context discovery & compilation. |
| **Groq Free Plan** | `llama-3.3-70b-versatile` | Documented org limits (e.g. 30 RPM, 1,000 RPD, 12k TPM). | Standard API terms; no training on API traffic. | **Secondary Candidate** for rapid static autopsy and classification. |
| **OpenRouter Free Tier** | `meta-llama/llama-3.3-70b-instruct:free` | $0 listed pricing; 20 RPM / 50 RPD limit without purchased credits. | Varies by upstream host; aggregator terms apply. | **Contingency / Fallback Route** only. |
| **Deterministic Mock Adapter** | `promptiq-mock-v1` | Unlimited local in-memory execution; zero external requests. | 100% private; zero network data transmission. | **Mandatory Standard** for automated CI/CD testing and unit test suites. |

---

## 4. Capacity Governor & Fair-Use Policy

To ensure equitable access across all users without incurring billable overage, PromptIQ enforces strict capacity governance:

1. **Per-User Token & Request Budgets**: Users are granted a sliding-window fair-use allocation (e.g. 30 requests per hour).
2. **Global Provider Pooling**: The system monitors total consumption against upstream provider daily and minute quotas.
3. **Graceful Queueing**: When provider concurrency limits are approached, incoming tasks are queued with transparent status updates to the user.
4. **Pause on Exhaustion**: If a zero-price quota is completely reached, PromptIQ informs the user honestly: *"PromptIQ capacity is currently paused due to high demand. Your request is queued and will resume shortly."* Under no circumstances will the system fail over to a paid endpoint or ask the user for a credit card or API key.
5. **Circuit Breaker**: Detects provider 429/503 errors and temporarily halts requests to that route, preventing cascade failures.
