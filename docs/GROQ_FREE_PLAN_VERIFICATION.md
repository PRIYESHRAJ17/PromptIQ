# PromptIQ Groq Free Plan Verification and Terms Audit

**Phase**: 3.4 Technical Qualification  
**Date**: November 21, 2026  
**Auditor**: Model Operations & Zero-Spend Governance Group  
**Primary Source**: Groq Documentation (`console.groq.com/docs/rate-limits`) & Groq Cloud Terms of Service  

---

## 1. Groq Free Tier vs Paid Developer Plan Distinction

To uphold PromptIQ's non-negotiable **₹0 / $0.00 operating cost invariant**, we audited Groq's billing architecture to ensure that free-tier endpoints cannot silently switch to paid rates:

| Dimension | Groq Free Plan (PromptIQ Eligible) | Groq Developer Plan (STRICTLY PROHIBITED) |
| :--- | :--- | :--- |
| **Pricing** | **$0.00 / token permanently** | \$0.15 / 1M input tokens, \$0.59 / 1M output tokens |
| **Credit Card on File** | **None required** | Credit card or billing agreement mandatory |
| **Quota Ceilings** | `openai/gpt-oss-120b`: 30 RPM, 1,000 RPD, 100k TPD<br>`openai/gpt-oss-20b`: 30 RPM, 14,400 RPD, 500k TPD | 1,000 RPM, 10M+ TPD |
| **Overage Behavior** | **HTTP 429 `rate_limit_exceeded` with `Retry-After` header**. Hard stop, zero financial charge. | Metered pay-as-you-go billing |
| **Automatic Upgrades?** | **NO**. Free plan accounts cannot be upgraded without explicit user credit card entry. | N/A |
| **PromptIQ Policy** | **VERIFIED ELIGIBLE** for internal hosted inference | **HARD BLOCKED** by `CostEligibilityGate` and `verify_zero_price_route` |

---

## 2. Model Identifier & Quota Analysis

### 2.1 Primary Candidate: `openai/gpt-oss-120b`
- **Model Identifier**: `openai/gpt-oss-120b`
- **Model Architecture**: Open-weight foundation reasoning model served on Groq LPU inference engines.
- **Context Window**: 131,072 tokens. Maximum output tokens: 4,096 tokens.
- **Free Quotas**:
  - Requests Per Minute (RPM): 30
  - Requests Per Day (RPD): 1,000
  - Tokens Per Minute (TPM): 8,000
  - Tokens Per Day (TPD): 100,000
- **Operational Constraint**: The 100,000 TPD ceiling requires token budgeting:
  - Average PromptIQ turn: ~1,000 tokens (700 input + 300 output).
  - Maximum daily capacity: ~100 full reasoning tasks per operator key.
  - Reserved strictly for complex synthesis, deep planning, and primary generation.

### 2.2 Secondary Candidate: `openai/gpt-oss-20b`
- **Model Identifier**: `openai/gpt-oss-20b`
- **Model Architecture**: Lightweight fast open-weight model on Groq LPUs.
- **Context Window**: 131,072 tokens. Maximum output tokens: 8,192 tokens.
- **Free Quotas**:
  - Requests Per Minute (RPM): 30
  - Requests Per Day (RPD): 14,400
  - Tokens Per Minute (TPM): 6,000
  - Tokens Per Day (TPD): 500,000
- **Role**: Secondary specialist, routine classification, fast filtering, and adversarial critic.
- **Multi-Model Relationship**: Both `openai/gpt-oss-120b` and `openai/gpt-oss-20b` belong to the `gpt-oss` family and execute on Groq infrastructure. This is multi-model collaboration, but **NOT** independent multi-provider or cross-family execution.

---

## 3. Data Privacy, Retention, and Terms of Service

1. **Model Training Terms**: Under the Groq Cloud Services Agreement, customer prompts, completions, and embeddings transmitted via the inference API are **not used** by Groq to train, retrain, or fine-tune models.
2. **Default Retention**: Customer inputs and outputs are processed in ephemeral memory and retained in transient security logs for **up to 30 days** solely for abuse detection, operational reliability, and rate-limit auditing.
3. **Zero Data Retention (ZDR)**: Groq offers Zero Data Retention for enterprise/commercial agreements. However, ZDR is **not active by default** on free-tier accounts. PromptIQ records this fact in `ProviderPrivacyCard` (`data_retention_days=30`) and forbids routing `RESTRICTED` compliance data to Groq.
4. **Data Residency**: Groq inference infrastructure and transient logging reside within the United States.
5. **Commercial Use**: Free-tier access is provided on an "AS-IS" basis for evaluation, prototyping, and application development without an SLA.
