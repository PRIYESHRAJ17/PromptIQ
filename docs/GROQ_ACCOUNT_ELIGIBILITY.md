# Groq Account & Model Eligibility Audit (Phase 3.4.1)
## Free Tier Entitlements, Model Identifiers, Quota Rules, and Account Verification

**Audit Date**: 2026-11-22  
**Target Provider**: GroqCloud (`https://api.groq.com/openai/v1`)  
**Investigated Models**: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`  
**Classification**: `OPERATOR_ATTESTED` / `IMPLEMENTED_NOT_LIVE_VERIFIED`  

---

## 1. Official Model Status & Endpoints

Groq supports open-weight model architectures running on its Language Processing Unit (LPU) hardware. Both candidate models were independently verified against official GroqCloud documentation:

| Parameter | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` |
|---|---|---|
| **Exact Identifier** | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` |
| **API Endpoint** | `https://api.groq.com/openai/v1/chat/completions` | `https://api.groq.com/openai/v1/chat/completions` |
| **Model Lifecycle Status** | **Production Supported** (Active) | **Production Supported** (Active) |
| **Preview Status** | **No** (Standard production catalog) | **No** (Standard production catalog) |
| **Context Window** | 131,072 tokens | 131,072 tokens |
| **Max Completion Tokens**| 65,536 tokens | 65,536 tokens |
| **Base Architecture** | GPT-OSS Mixture of Experts / Dense Transformer | GPT-OSS Small Footprint Specialist |
| **Licensing** | Open Weights / Apache 2.0 compatible | Open Weights / Apache 2.0 compatible |
| **Geographic Availability**| Global, fully accessible from India | Global, fully accessible from India |

---

## 2. Free Plan vs. Developer Plan: Critical Quota Distinction

Groq operates two strictly distinct tiers. Quotas from Developer/Paid tiers must never be conflated with the cardless Free Plan:

### 2.1 Free Plan Entitlements (Zero Payment Method Required)
- **Payment Method**: None required to sign up or create API keys.
- **`openai/gpt-oss-120b` Limits**:
  - **RPM (Requests Per Minute)**: 30
  - **RPD (Requests Per Day)**: 1,000
  - **TPM (Tokens Per Minute)**: 8,000
  - **TPD (Tokens Per Day)**: 200,000
- **`openai/gpt-oss-20b` Limits**:
  - **RPM (Requests Per Minute)**: 30
  - **RPD (Requests Per Day)**: 1,000
  - **TPM (Tokens Per Minute)**: 8,000
  - **TPD (Tokens Per Day)**: 200,000
- **Token Price**: **$0.00 / ₹0**
- **Overage Behavior**: Hard stop. The API returns HTTP `429 Too Many Requests` (`error.code: rate_limit_exceeded`). Requests are dropped until the rate limit window resets.
- **Auto-Upgrade**: **None**. Free accounts cannot be automatically transitioned to paid billing unless an operator manually navigates to the Billing console and adds a valid credit card.

### 2.2 Developer Plan Entitlements (Paid Tier - Strictly Ineligible for PromptIQ)
- **Payment Method**: Credit card required.
- **Rate Limits**: 1,000 RPM, 250,000 TPM.
- **Pricing**: Pay-per-token model ($0.15 - $0.70 / 1M tokens depending on model size).
- **PromptIQ Eligibility**: **STRICTLY REJECTED**. PromptIQ prohibits paid inference or unapproved operator spend.

---

## 3. Important Quota Enforcement Rules

1. **Organization-Level Scope**:
   - Rate limits are shared across the entire Groq organization. All API keys generated within an organization draw from the same shared 1,000 RPD and 8,000 TPM pool.
2. **Sliding Minute Window**:
   - The TPM limit uses a continuous sliding 60-second window, not a discrete clock-minute reset.
3. **The 8,000 TPM Constraint**:
   - Because Free tier TPM is 8,000, sending a single large prompt (e.g., 6,000 input tokens + 2,500 expected output tokens) will immediately trigger an HTTP 429, even if 0 requests were made that day.
   - PromptIQ's smoke tests and pilot prompts must enforce a strict `max_tokens: 512` and compact input representations to prevent premature TPM exhaustion.

---

## 4. Operator Account Verification States

A basic environment variable check is insufficient to prove account status. PromptIQ enforces a 6-tier account verification hierarchy:

| State | Definition | Permitted Actions in PromptIQ |
|---|---|---|
| `UNVERIFIED` | No credentials or account details configured. | All live requests blocked; fail closed with `BLOCKED_EXTERNAL`. |
| `OPERATOR_ATTESTED` | Operator declared free plan in local config without dashboard proof. | Synthetic local tests only; not eligible for production routing. |
| `DASHBOARD_EVIDENCED`| Operator inspected Groq Console "Limits & Billing" page and confirmed Free tier. | Local live smoke tests permitted with explicit `--opt-in`. |
| `PROVIDER_CONFIRMED` | API metadata or billing headers confirm 0-cost plan. | Single-request live tests approved. |
| `INELIGIBLE_PAID` | Account has credit card or active paid plan attached. | **PERMANENTLY REJECTED**; live requests blocked to prevent billing. |
| `VERIFIED_FREE_ACCOUNT`| Confirmed cardless, hard-stop verified, non-retraining terms. | Full zero-cost multi-model workflow approved. |

### Operator Verification Checklist:
To achieve `DASHBOARD_EVIDENCED` or `VERIFIED_FREE_ACCOUNT`:
1. Log in to [Groq Console](https://console.groq.com).
2. Navigate to **Settings > Billing**.
3. Verify that **No Payment Method** is listed.
4. Navigate to **Settings > Limits**.
5. Verify that your organization tier is listed as **Free Plan** with 1,000 RPD for GPT-OSS models.
6. Set `PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED=true` in local environment.
