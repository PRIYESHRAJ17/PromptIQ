# PromptIQ Provider Terms and Privacy Audit
## Comprehensive Legal, Data Governance, and Audience Restriction Analysis

**Audit Revision**: 2026.11-v3.3  
**Date**: November 21, 2026  
**Auditor**: Data Protection, Privacy & Legal Compliance Office  
**Invariant**: Zero user leakage, complete data provenance, zero BYOK, and non-negotiable zero user cost.

---

## 1. Provider Terms and Legal Agreements Matrix

| Provider | Governing Agreement | Commercial Production Permitted? | Model Training on API Traffic? | Human Review of Prompts? | Audience & Age Restrictions | Primary Privacy Rating |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Google AI Studio** | Gemini API Additional Terms of Service | Yes (Developer API terms) | **Yes** (Free tier used for model training) | **Yes** (Human reviewers access data) | **Strictly $\ge 18$ Years Old** (Forbidden for minors) | `RESTRICTED_DATA_EXCLUDED` |
| **GroqCloud** | Groq Cloud Services Agreement & Terms | Yes (AS-IS basis) | **No** (Zero training on API data) | **No** (Automated abuse filtering only) | Standard 18+ operator | `CONFIDENTIAL_APPROVED` |
| **Cloudflare Workers AI** | Cloudflare Service Terms | Yes | **No** (Zero training on API data) | **No** | Standard | `CONFIDENTIAL_APPROVED` |
| **OpenRouter** | OpenRouter Terms of Service | Variable (Proxy) | Variable upstream | Variable upstream | Standard | `RESTRICTED_DATA_EXCLUDED` |
| **NVIDIA NIM** | NVIDIA Developer Program Agreement | **No** (Research/dev only) | Unknown | Unknown | Standard | `NON_COMMERCIAL_ONLY` |
| **Mistral AI** | Mistral Non-Production License (MNPL) | **No** (Non-production only) | Unknown | Unknown | Standard | `NON_COMMERCIAL_ONLY` |
| **Cohere** | Cohere Terms of Use (Trial API) | **No** (Evaluation only) | Unknown | Unknown | Standard | `NON_COMMERCIAL_ONLY` |

---

## 2. In-Depth Privacy and Terms Analysis

### 2.1 Google Gemini Developer API (Google AI Studio)
- **Governing Document**: Google APIs Terms of Service & Gemini API Additional Terms.
- **Model Training Policy**: Prompts, completions, and fine-tuning data submitted under the free tier of the Gemini Developer API are retained and used by Google to develop, improve, and train Google machine learning models and enterprise features.
- **Human Review**: Google's terms explicitly notify users that human reviewers may read, annotate, and process free-tier prompts and responses.
- **Age Restriction Clause**: Under Section "Age Requirements", developers must be at least 18 years old to access the APIs, and **must not use the services as part of any website, application, or service directed towards or likely to be accessed by individuals under the age of 18**.
- **PromptIQ Enforcement**:
  - `DataSensitivityLevel.CONFIDENTIAL` and `RESTRICTED` are strictly blocked from Google endpoints.
  - If a task or project targets minors or students under 18, Google routes are hard-blocked by `PrivacyGovernanceService.validate_audience_terms()`.
  - Eligible only for `PUBLIC` and `GENERAL` data where users are confirmed adults.

---

### 2.2 GroqCloud
- **Governing Document**: Groq Cloud Services Agreement (2026 Revision).
- **Model Training Policy**: Groq explicitly states that it does not use customer data (prompts, completions, embeddings) transmitted through the inference API to train, retrain, or improve base models.
- **Data Retention**: Prompts and completions are held in temporary memory during processing and retained in transient security logs for up to 30 days solely for rate limiting, billing auditing, and legal compliance/abuse monitoring.
- **Production Use**: Allowed under developer/free terms, provided the user accepts that free-tier capacity has no uptime SLA and is subject to dynamic rate throttling.
- **PromptIQ Enforcement**:
  - Approved for `DataSensitivityLevel.PUBLIC`, `GENERAL`, and `CONFIDENTIAL`.
  - Primary provider for confidential proprietary prompts, competitive system instructions, and sensitive codebases.

---

### 2.3 Cloudflare Workers AI
- **Governing Document**: Cloudflare Privacy Notice and Terms of Service.
- **Model Training Policy**: Cloudflare does not use customer content passing through Workers AI for model training. Prompts are processed ephemerally on edge GPUs.
- **PromptIQ Enforcement**:
  - Approved for `DataSensitivityLevel.GENERAL` and `CONFIDENTIAL` tasks within the 10,000 Neurons/day ceiling.

---

## 3. PromptIQ 4-Tier Data Classification & Routing Matrix

PromptIQ enforces strict mathematical sensitivity ordering:
$$\text{PUBLIC} (0) < \text{GENERAL} (1) < \text{CONFIDENTIAL} (2) < \text{RESTRICTED} (3)$$

```
                                 [ Incoming Task Data ]
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
             Is Data Sensitivity RESTRICTED?        Is Data Sensitivity CONFIDENTIAL?
                         │                                   │
              YES ───────┴──────── NO             YES ───────┴──────── NO
               │                    │              │                    │
               ▼                    ▼              ▼                    ▼
     [ Internal Engine Only ]  [ Continue ]  [ Groq Only ]        [ Google, Groq, ]
     - In-memory execution                   - No model training  [ or OpenRouter ]
     - Zero external egress                  - Human review barred
     - promptiq-mock-v1                      - openai/gpt-oss-120b
```

| Sensitivity Level | Permitted Providers | Forbidden Providers | Enforcement Action |
| :--- | :--- | :--- | :--- |
| **`PUBLIC`** (0) | Google, Groq, Cloudflare, OpenRouter, Mock | None | Standard dynamic model routing. |
| **`GENERAL`** (1) | Google, Groq, Cloudflare, OpenRouter, Mock | None | Standard dynamic model routing (requires 18+ audience for Google). |
| **`CONFIDENTIAL`** (2) | **Groq**, Cloudflare, Mock | **Google**, OpenRouter | Google is blocked due to human review and training terms. Routed to Groq. |
| **`RESTRICTED`** (3) | **Internal Engine (`mock`) only** | **All External Free APIs** | All external HTTP calls blocked. Air-gapped in-memory execution only. |
