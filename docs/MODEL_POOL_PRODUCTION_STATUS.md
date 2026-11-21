# PromptIQ Model Pool Production Status Ledger

**Phase**: 3.4 Production Hardening  
**Date**: November 21, 2026  
**Auditor**: Model Pool Governance & Architectural Integrity Board  

---

## 1. Production Model Pool Status Ledger

| Model Identifier | Provider & Family | Eligibility State | Production Routing Status | Primary Assigned Roles | Verification Evidence & Constraints |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **`openai/gpt-oss-120b`** | Groq (`gpt-oss`) | **`VERIFIED_ELIGIBLE`** | **ACTIVE PRODUCTION** | `ORCHESTRATOR`, `REASONING`, `PROMPT_ENGINEER`, `RESEARCH` | Verified $0 on GroqCloud Free Plan. 1,000 RPD, 100k TPD. Safe for CONFIDENTIAL data (no model training). |
| **`openai/gpt-oss-20b`** | Groq (`gpt-oss`) | **`VERIFIED_ELIGIBLE`** | **ACTIVE PRODUCTION** | `FAST`, `CRITIC`, `VERIFIER` | Verified $0 on GroqCloud Free Plan. 14,400 RPD, 500k TPD. Sub-second execution. Critic role requires disclosure of same-family intra-provider status. |
| **`promptiq-mock-v1`** | Internal (`internal`) | **`VERIFIED_ELIGIBLE`** | **ACTIVE PRODUCTION** | `RESTRICTED_AIRGAP`, `DETERMINISTIC_TESTING` | In-memory deterministic engine. Unlimited quota. Zero external network egress. Safe for all data tiers. |
| **`gemini-3.8-flash`** | Google (`gemini`) | **`CONDITIONALLY_ELIGIBLE`** | **RESTRICTED CONDITIONAL** | `ADULT_DEVELOPER_ONLY` | Excluded from general production due to terms barring minor-directed access (<18) and free-tier prompt logging for model training. |
| **`gemini-3.5-flash-lite`**| Google (`gemini`) | **`CONDITIONALLY_ELIGIBLE`** | **RESTRICTED CONDITIONAL** | `ADULT_DEVELOPER_FAST` | Excluded from general production. |
| **`gemini-2.5-flash`** | Google (`gemini`) | **`CONDITIONALLY_ELIGIBLE`** | **RESTRICTED CONDITIONAL** | `ADULT_DEVELOPER_SECONDARY` | Excluded from general production. |
| **`qwen/qwen3.8-27b`** | Groq (`qwen`) | **`REVIEW_REQUIRED`** | **ISOLATED EVALUATION ONLY** | `EXPERIMENTAL_EVAL` | **Demoted per Phase 3.4 Directive**: Preview/experimental model on Groq. Barred from production routes to prevent runtime instability. |
| **`@cf/meta/llama-3.1-8b-instruct`**| Cloudflare (`llama`) | **`CONDITIONALLY_ELIGIBLE`** | **STANDBY EDGE CLASSIFIER** | `EDGE_FAST_CLASSIFIER` | 10,000 Neurons/day free allowance on Cloudflare Workers AI. Secondary fast classifier only. |
| **`meta-llama/llama-3.3-70b-instruct:free`**| OpenRouter (`llama`) | **`CONDITIONALLY_ELIGIBLE`** | **TERTIARY FAILOVER ONLY** | `TERTIARY_FAILOVER` | Subject to severe 50 RPD account ceiling for cardless accounts and variable upstream latency. |
| **`gemini-2.0-flash`** | Google (`gemini`) | **`RETIRED`** | **PERMANENTLY BLOCKED** | None | Officially shut down by Google on June 1, 2026. Hard-blocked by gateway. |
| **`llama-3.3-70b-versatile`**| Groq (`llama`) | **`RETIRED`** | **PERMANENTLY BLOCKED** | None | Retired on GroqCloud endpoints in 2026. Hard-blocked by gateway. |
| **`llama-3.1-8b-instant`**| Groq (`llama`) | **`RETIRED`** | **PERMANENTLY BLOCKED** | None | Retired on GroqCloud endpoints in 2026. Hard-blocked by gateway. |
| **`qwen-2.5-coder-32b`** | Groq (`qwen`) | **`RETIRED`** | **PERMANENTLY BLOCKED** | None | Retired on GroqCloud endpoints in 2026. Hard-blocked by gateway. |

---

## 2. Rationales for Phase 3.4 Status Adjustments

### 2.1 Demotion of Groq Qwen 3.8 27B to Evaluation Only (`REVIEW_REQUIRED`)
In Phase 3.3, Qwen 3.8 27B was proposed as a coding/verifier model. However, Groq's official API status classifies Qwen 3.8 27B as an **experimental preview model**. Preview endpoints on serverless LPU clouds are subject to unannounced deprecation, quota fluctuations, and model weight swapping.
- **Enforcement**: Per Phase 3.4 directives, preview models must never be silently promoted to production. Qwen 3.8 27B is isolated to evaluation environments (`ineligible_use_cases=["production_routing", "production_verification"]`).

### 2.2 Qualification of Gemini Developer API as Conditional (`CONDITIONALLY_ELIGIBLE`)
Gemini 3.8 Flash was previously considered for the general primary orchestrator role. A critical legal review of the Gemini API Additional Terms revealed that developers must not direct applications towards or permit access by individuals under 18 years of age.
- **Application Reality**: PromptIQ is built for students, aspiring developers, researchers, and general public users. Narrowing the application's target audience to satisfy one provider's terms is rejected.
- **Enforcement**: Gemini models are reclassified as `CONDITIONALLY_ELIGIBLE`. They are active only in verified adult developer environments and excluded from general public production routes.

---

## 3. Seven Logical Model Roles Production Assignment

With Qwen 3.8 preview-isolated and Gemini conditional, PromptIQ's active production roles are mapped to verified zero-price models:

| Role | Primary Assigned Model | Backup / Failover Model | Rationale |
| :--- | :--- | :--- | :--- |
| **`ORCHESTRATOR`** | `openai/gpt-oss-120b` (Groq) | `promptiq-mock-v1` (Internal) | High reasoning, tool calling, 128k context window. |
| **`REASONING`** | `openai/gpt-oss-120b` (Groq) | `promptiq-mock-v1` (Internal) | Deep reasoning on complex logic and architecture. |
| **`FAST`** | `openai/gpt-oss-20b` (Groq) | `promptiq-mock-v1` (Internal) | High throughput (14,400 RPD), sub-second latency. |
| **`RESEARCH`** | `openai/gpt-oss-120b` (Groq) | `promptiq-mock-v1` (Internal) | Document synthesis, evidence tracing, 128k context. |
| **`PROMPT_ENGINEER`**| `openai/gpt-oss-120b` (Groq) | `promptiq-mock-v1` (Internal) | Structured compilation of target-native prompts. |
| **`CRITIC`** | `openai/gpt-oss-20b` (Groq) | `promptiq-mock-v1` (Internal) | Adversarial flaw detection. Requires intra-family disclosure. |
| **`VERIFIER`** | `openai/gpt-oss-20b` (Groq) | `promptiq-mock-v1` (Internal) | Structured JSON verification and deterministic invariant checks. |
