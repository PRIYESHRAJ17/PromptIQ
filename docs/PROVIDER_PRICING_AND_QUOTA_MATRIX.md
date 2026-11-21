# PromptIQ Provider Pricing and Quota Matrix

**Revision**: 2026.11-v3.3  
**Audit Date**: November 21, 2026  
**Auditor**: Model Operations & Zero-Spend Governance Board  

---

## 1. Zero-Price Inference Quotas & Rate Limits

This matrix documents the exact verified rate limits and throughput ceilings for all eligible zero-price models.

| Provider | Model Identifier | RPM | RPD | TPM | TPD | Reset Interval | Overage / Quota Exhaustion Behavior |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Google AI Studio** | `gemini-3.8-flash` | 15 | 1,500 | 1,000,000 | 10,000,000 | Daily at 00:00 UTC | HTTP 429 `RESOURCE_EXHAUSTED`. Hard stop, zero financial charge. |
| **Google AI Studio** | `gemini-3.5-flash-lite` | 30 | 1,500 | 1,000,000 | 10,000,000 | Daily at 00:00 UTC | HTTP 429 `RESOURCE_EXHAUSTED`. Hard stop, zero financial charge. |
| **Google AI Studio** | `gemini-2.5-flash` | 15 | 1,500 | 1,000,000 | 10,000,000 | Daily at 00:00 UTC | HTTP 429 `RESOURCE_EXHAUSTED`. Hard stop, zero financial charge. |
| **GroqCloud** | `openai/gpt-oss-120b` | 30 | 1,000 | 8,000 | 100,000 | Daily at 00:00 UTC | HTTP 429 with `Retry-After`. Hard stop, zero financial charge. |
| **GroqCloud** | `openai/gpt-oss-20b` | 30 | 14,400 | 6,000 | 500,000 | Daily at 00:00 UTC | HTTP 429 with `Retry-After`. Hard stop, zero financial charge. |
| **GroqCloud** | `qwen/qwen3.8-27b` | 30 | 1,000 | 6,000 | 100,000 | Daily at 00:00 UTC | HTTP 429 with `Retry-After`. Hard stop, zero financial charge. |
| **Cloudflare Workers AI** | `@cf/meta/llama-3.1-8b-instruct` | 100 | ~2,000 | 50,000 | ~200,000 | Daily at 00:00 UTC (10k Neurons/day) | API returns error. Free plan hard stops; cannot be auto-billed. |
| **OpenRouter** | `:free` models (aggregate) | 20 | 50 | 5,000 | 50,000 | Daily rolling | HTTP 429. Hard stop on 50 RPD account ceiling for cardless accounts. |
| **Internal Engine** | `promptiq-mock-v1` | 10,000 | 1,000,000 | 10,000,000 | 100,000,000 | None (In-memory) | Never exhausts. Air-gapped fallback for deterministic testing. |

---

## 2. Ineligible Providers: Pricing and Billing Traps

| Provider | Quota Offered | Billing Requirement | Financial Trap & Reason for Ineligibility |
| :--- | :--- | :--- | :--- |
| **Cerebras** | \$5 trial credit | Credit card mandatory | Promotional credit expires after 30 days. Automatically begins charging pay-as-you-go rates (\$0.60/MTok) once credits deplete. Violates Gate B & E. |
| **SambaNova** | 20 RPD without card | Credit card required for developer tier | 20 RPD is inadequate for production. Adding credit card unlocks developer tier with paid per-token charges. Violates Gate C & E. |
| **Together AI** | None | \$15 minimum upfront deposit | Pay-as-you-go only. Violates Gate B & E. |
| **DeepInfra** | \$5 credit | \$10 minimum card deposit | Credit card required for production. Violates Gate B & E. |
| **Mistral AI** | Free evaluation | Credit card for production | Production user interactions require paid account. Free Codestral under MNPL is non-production. Violates Gate D. |
| **Cohere** | 1,000 calls/month trial | Credit card for production | Production use strictly forbidden on trial keys. Violates Gate D. |
| **NVIDIA NIM** | 1,000 credits trial | Commercial license required | Free endpoints are non-commercial evaluation only. Production requires \$4,500/GPU/yr license. Violates Gate D. |

---

## 3. Capacity Governor & Token Conservation Strategy

Because Groq imposes a strict **100,000 Tokens Per Day (TPD)** ceiling on flagship models (`openai/gpt-oss-120b` and `qwen/qwen3.8-27b`), PromptIQ implements an intelligent token conservation strategy:

1. **Token Budgeting per Task**:
   - Discovery Turns: Capped at 500 input tokens / 250 output tokens.
   - Prompt Compilation: Capped at 1,500 input tokens / 1,000 output tokens.
   - Prompt Autopsy: Capped at 1,200 input tokens / 800 output tokens.
2. **Fast-Model Routing for Small Tasks**:
   - Routine classification and schema validation route to `openai/gpt-oss-20b` (500,000 TPD allowance) or `gemini-3.5-flash-lite` (10,000,000 TPD allowance).
   - Flagship 120B reasoning models are reserved strictly for synthesis and critical review.
3. **Local Sliding-Window Quota Tracking**:
   - The `CapacityGovernor` tracks local consumption across 60-second and 86,400-second windows.
   - When 95% of any limit is reached, the governor proactively queues non-urgent tasks and returns HTTP 429 with explicit `Retry-After`, preventing uncoordinated provider rejections.
