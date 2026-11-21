# PromptIQ Provider Feasibility Audit
## Exhaustive 22-Point Zero-Price Hosted Inference Provider Investigation

**Audit Date**: November 21, 2026  
**Auditor**: Model Intelligence Operations & Production Feasibility Group  
**Target Environment**: Production Zero-Spend Architecture  
**Strict Invariant**: Zero user charges (₹0 / $0.00), no BYOK, no user API keys, no local GPU/Ollama dependency, and no paid fallback routes.

---

## 1. Executive Summary & Provider Feasibility Matrix

We conducted primary-source investigations into 12 major cloud AI inference providers to identify which combinations genuinely satisfy PromptIQ's non-negotiable requirements:
1. **$0.00 / token cost** permanently.
2. **No credit card or billing instrument** required on file.
3. **Native hard stop** (reject with 429 when quota is reached, never charge).
4. **Commercial and production terms compatibility**.
5. **Multi-model and multi-provider independence**.

| # | Provider | Free Tier Present? | Credit Card Required? | Permanent Free Tier? | Overage Hard Stop? | Commercial / Production Terms? | Training on Free Data? | Audience / Age Limits | Formal Gate Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **Google AI Studio (Gemini)** | Yes | **No** | **Yes** | **Yes** (429) | Yes (Developer API) | **Yes** (Human review) | **18+ Only** (No minors) | **`CONDITIONALLY_ELIGIBLE`** |
| 2 | **GroqCloud** | Yes | **No** | **Yes** | **Yes** (429) | Yes (AS-IS POC/Prod) | **No** (Zero training) | 18+ operator | **`VERIFIED_ELIGIBLE`** |
| 3 | **Cloudflare Workers AI** | Yes (10k N/d) | **No** | **Yes** | **Yes** (Error) | Yes (Standard Free) | **No** (No training) | Standard | **`CONDITIONALLY_ELIGIBLE`** |
| 4 | **OpenRouter** | Yes (:free) | **No** | **Yes** (50 RPD) | **Yes** (429) | Variable | Variable | Standard | **`CONDITIONALLY_ELIGIBLE`** |
| 5 | **Cerebras** | Trial only | **Yes** ($5 trial) | **No** (30 days) | **No** (Auto-charges) | Yes | Unknown | Standard | **`INELIGIBLE_BILLING`** |
| 6 | **SambaNova** | 20 RPD only | Card for dev | **No** (20 RPD) | Paid if card linked| Commercial | Unknown | Standard | **`INELIGIBLE_TERMS`** |
| 7 | **NVIDIA NIM** | Yes (Free key) | **No** | Limited | **Yes** | **No (Non-commercial)** | Unknown | Standard | **`INELIGIBLE_TERMS`** |
| 8 | **Mistral AI** | Free evaluation | **No** | Limited | Paid per token | **No (MNPL License)** | Unknown | Standard | **`INELIGIBLE_TERMS`** |
| 9 | **Cohere** | Trial key (1k/mo) | Card for prod | **No** (Trial) | Paid per token | **No (Non-production)**| Unknown | Standard | **`INELIGIBLE_TERMS`** |
| 10 | **Together AI** | **No** | **Yes** ($15 min) | **No** | Paid per token | Commercial | Commercial | Standard | **`INELIGIBLE_PAID`** |
| 11 | **DeepInfra** | Trial only ($5) | **Yes** ($10 card) | **No** | Paid per token | Commercial | Commercial | Standard | **`INELIGIBLE_PAID`** |
| 12 | **Hugging Face** | ~$0.10/mo | Card for prod | **No** | Paid per token | Pro required | Variable | Standard | **`INELIGIBLE_PAID`** |

---

## 2. In-Depth Provider Audits

### 2.1 Google Gemini Developer API (Google AI Studio)
- **Primary Source**: `https://ai.google.dev/gemini-api/docs/pricing` & `https://ai.google.dev/terms`
- **Active Models**: `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`.
- **Pricing**: $0.00 / token on Developer API free tier. Paid pay-as-you-go requires explicit Google Cloud project billing attachment (prohibited).
- **Rate Limits**: 15 RPM, 1,500 RPD, 1,000,000 TPM for `gemini-3.8-flash`. 30 RPM, 1,500 RPD for `gemini-3.5-flash-lite`.
- **Credit Card Requirement**: None. Google account only.
- **Overage Behavior**: Hard stop (HTTP 429 `RESOURCE_EXHAUSTED`). No billing risk.
- **Data Privacy & IP**: Under Google AI Studio free tier terms: *"Google uses this data, subject to our Privacy Policy, to provide, improve, and develop Google products and services and machine learning technologies, including Google's enterprise features."* Human reviewers may read prompts and completions. Rejects CONFIDENTIAL and RESTRICTED data.
- **Audience & Age Restriction**: Under Gemini API Additional Terms (Section "Age Requirements"): Users must be at least 18 years of age. Developers **must not** direct applications towards or allow access by individuals under 18 years old.
- **Production Terms**: Permitted under Developer API terms, but subject to free quotas and "AS-IS" availability.
- **Gate Verdict**: **`CONDITIONALLY_ELIGIBLE`** (General data only; strictly $\ge 18$ audience; failover to Groq/mock for confidential data).

---

### 2.2 GroqCloud
- **Primary Source**: `https://console.groq.com/docs/rate-limits` & `https://groq.com/terms-of-service/`
- **Active Models**: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`.
- **Retired Models**: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen-2.5-coder-32b` (Retired late 2026).
- **Pricing**: $0.00 / token on free plan. Paid Developer Plan exists ($0.59/MTok output) with 1,000 RPM, but is strictly isolated and excluded.
- **Rate Limits**:
  - `openai/gpt-oss-120b`: 30 RPM, 1,000 RPD, 8,000 TPM, 100,000 TPD.
  - `openai/gpt-oss-20b`: 30 RPM, 14,400 RPD, 6,000 TPM, 500,000 TPD.
  - `qwen/qwen3.8-27b`: 30 RPM, 1,000 RPD, 6,000 TPM, 100,000 TPD.
- **Credit Card Requirement**: None on free plan.
- **Overage Behavior**: Hard stop (HTTP 429 with `Retry-After` header). Capacity governor tracks quotas locally and pauses before exhaustion.
- **Data Privacy & IP**: Groq does not use customer API inputs/outputs to train models. Retention is 30 days solely for security monitoring. Safe for CONFIDENTIAL data.
- **Audience Restrictions**: Standard commercial terms (operator $\ge 18$). Allows general audiences.
- **Production Terms**: Permitted for production prototypes and applications on an AS-IS basis without SLA.
- **Gate Verdict**: **`VERIFIED_ELIGIBLE`** (Primary reasoning, coding, and confidential workflow engine).

---

### 2.3 Cloudflare Workers AI
- **Primary Source**: `https://developers.cloudflare.com/workers-ai/platform/pricing/`
- **Active Models**: `@cf/meta/llama-3.1-8b-instruct`, `@cf/mistral/mistral-7b-instruct-v0.2`.
- **Pricing**: 10,000 Neurons/day free on Cloudflare free account.
- **Capacity**: ~200,000 tokens/day throughput under 10k Neurons. Resets daily at 00:00 UTC.
- **Credit Card Requirement**: None for free plan.
- **Overage Behavior**: Hard stop. When daily 10,000 Neurons are exhausted, calls fail with error code. Free plans cannot be auto-billed.
- **Data Privacy & IP**: Cloudflare does not retain customer prompts or completions for model training.
- **Limitations**: Larger 70B+ models require a paid Workers subscription ($5/mo).
- **Gate Verdict**: **`CONDITIONALLY_ELIGIBLE`** (Fast edge classifier and routing pre-filter only).

---

### 2.4 OpenRouter
- **Primary Source**: `https://openrouter.ai/docs/limits` & `https://openrouter.ai/terms`
- **Active Models**: `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-r1:free`, `baidu/ernie-5.5-flash-preview:free`.
- **Pricing**: $0.00 / token on `:free` variants.
- **Account Quota**: Accounts with $<\$10$ lifetime purchases are strictly capped at **50 Requests Per Day** across all free models.
- **Credit Card Requirement**: None for free usage.
- **Overage Behavior**: Hard stop (HTTP 429).
- **Data Privacy & IP**: Variable upstream logging; intermediary logging. Ineligible for CONFIDENTIAL data.
- **Gate Verdict**: **`CONDITIONALLY_ELIGIBLE`** (Tertiary failover only; severe 50 RPD limit prevents primary role).

---

### 2.5 Cerebras
- **Primary Source**: `https://inference-docs.cerebras.ai/pricing`
- **Candidate Evaluated**: `llama-3.3-70b` on Cerebras fast inference.
- **Findings**: Cerebras offers a promotional $5 free trial credit that expires after 30 days. To obtain the key or continue usage, a valid credit card must be linked. Upon credit depletion, accounts automatically transition to metered pay-as-you-go billing ($0.60/MTok output).
- **Ineligibility Reason**: Violates Gate B (no permanent free tier) and Gate E (requires credit card, auto-converts to paid billing).
- **Gate Verdict**: **`INELIGIBLE_BILLING`**.

---

### 2.6 SambaNova
- **Primary Source**: `https://cloud.sambanova.ai/pricing`
- **Candidate Evaluated**: `Meta-Llama-3.3-70B-Instruct`.
- **Findings**: The cardless free tier is throttled to an unusable **20 Requests Per Day (RPD)**. Adding a credit card removes the 20 RPD cap but converts the workspace to the paid Developer tier ($/token).
- **Ineligibility Reason**: 20 RPD is inadequate for production multi-model collaboration (a single multi-turn design session consumes 10-15 calls). Adding billing violates zero-cost invariant.
- **Gate Verdict**: **`INELIGIBLE_TERMS`**.

---

### 2.7 NVIDIA NIM (`build.nvidia.com`)
- **Primary Source**: `https://build.nvidia.com/` & NVIDIA Developer Program Agreement
- **Candidate Evaluated**: `meta/llama-3.3-70b-instruct`.
- **Findings**: Free API keys on `build.nvidia.com` are strictly restricted by NVIDIA terms to personal research, development, and evaluation. Deployment in a production service available to external users violates the license unless an NVIDIA AI Enterprise subscription ($4,500/GPU/yr) is purchased.
- **Ineligibility Reason**: Violates Gate D (Non-commercial / evaluation license only).
- **Gate Verdict**: **`INELIGIBLE_TERMS`**.

---

### 2.8 Mistral AI (La Plateforme)
- **Primary Source**: `https://mistral.ai/terms/` & Mistral Non-Production License (MNPL)
- **Candidate Evaluated**: `codestral-2501`.
- **Findings**: Codestral and free endpoint access are governed by the MNPL, which explicitly prohibits production user-facing interactions. Production API access requires a pay-as-you-go credit card account.
- **Gate Verdict**: **`INELIGIBLE_TERMS`**.

---

### 2.9 Cohere
- **Primary Source**: `https://cohere.com/pricing` & `https://cohere.com/terms-of-use`
- **Candidate Evaluated**: `command-r-plus`.
- **Findings**: Trial API keys are hard-capped at 1,000 calls per month and strictly forbid commercial or production use. Production keys require credit card pay-as-you-go.
- **Gate Verdict**: **`INELIGIBLE_TERMS`**.

---

### 2.10 Together AI, DeepInfra, and Hugging Face
- **Together AI**: Requires a minimum $15 upfront deposit. No permanent free tier. **`INELIGIBLE_PAID`**.
- **DeepInfra**: $5 trial credit only, requires a $10 deposit for production. **`INELIGIBLE_PAID`**.
- **Hugging Face**: Free tier allowance is negligible (~$0.10/mo) and quickly throttles. **`INELIGIBLE_PAID`**.

---

## 3. Verified Multi-Model Combinations

Based on exhaustive empirical and primary-source findings, the **only viable production combination** that preserves zero-spend, permanent free tier, and hard stops is:

1. **Combination A: Public / General Data & Adult Audience ($\ge 18$)**:
   - **Orchestrator & Synthesizer**: Google `gemini-3.8-flash` (1,500 RPD, 1M TPM).
   - **Reasoning & Independent Critic**: Groq `openai/gpt-oss-120b` (1,000 RPD, 100k TPD).
   - **Coding & Adapters**: Groq `qwen/qwen3.8-27b` (1,000 RPD, 100k TPD).
   - **Fast Edge Classifier**: Groq `openai/gpt-oss-20b` (14,400 RPD) or Cloudflare `llama-3.1-8b` (10k Neurons/d).
   - *Independence*: Full multi-provider (Google + Groq) and multi-family (Gemini + gpt-oss + Qwen).

2. **Combination B: Confidential IP Data or Unknown / Minor Audience**:
   - **Generator / Prompt Engineer**: Groq `openai/gpt-oss-120b` (1,000 RPD).
   - **Independent Critic**: Groq `qwen/qwen3.8-27b` (1,000 RPD) — separate model family (Qwen vs GPT-OSS).
   - **Fast Burst**: Groq `openai/gpt-oss-20b` (14,400 RPD).
   - *Independence*: Intra-provider, multi-family. Google is disqualified due to data training and minor restrictions. The audit trail explicitly records `consensus_status="single_provider_disclosed"`.

3. **Combination C: Air-Gapped / Restricted Compliance Data**:
   - **Execution**: Internal `promptiq-mock-v1` deterministic engine. Zero external egress.
