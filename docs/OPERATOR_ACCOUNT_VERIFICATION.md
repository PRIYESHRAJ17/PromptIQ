# Operator Account Verification & Console Audit Ledger (Phase 3.4.2)
## Independent Verification of Groq Cloud Free Plan Tier and Organization Quotas

**Audit Date**: 2026-11-22  
**Target Provider**: GroqCloud (`https://console.groq.com`)  
**Investigated Models**: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`  
**Current Account Verification State**: `BLOCKED_EXTERNAL` (Operator Dashboard Verification Required; No Credentials Injected in Current Workspace)  

---

## 1. Why Provider HTTP 200 Does Not Prove Free Tier

A foundational principle of PromptIQ's cost governance is that **an API returning HTTP 200 is NOT evidence that an inference request was free**:
1. Groq's API endpoint (`https://api.groq.com/openai/v1/chat/completions`) is structurally identical for both Free Plan and Developer (Paid) accounts.
2. The response body and headers do not contain a `"plan_tier": "free"` field.
3. If an operator inadvertently has a credit card attached to their Groq organization, the API will happily return HTTP 200 while accruing pay-as-you-go token debt.
4. Therefore, **the operator must manually audit the Groq Console** before executing live requests.

---

## 2. Six-Tier Account Verification Hierarchy

PromptIQ strictly separates these verification states:

| Verification State | Criteria & Evidence | Allowed Operations in PromptIQ |
|---|---|---|
| **`UNVERIFIED`** | Default state; no credentials or account confirmation provided. | All live calls blocked; fail closed with `BLOCKED_EXTERNAL`. |
| **`OPERATOR_ATTESTED`** | Operator configured environment variable without dashboard screenshot/log. | Synthetic local tests only; marked `COST_UNVERIFIED`. |
| **`DASHBOARD_EVIDENCED`**| Operator logged into Groq Console and confirmed "No payment method" and "Free Plan". | Single-request smoke tests permitted with explicit opt-in. |
| **`PROVIDER_CONFIRMED`** | Provider billing metadata or official invoice confirms $0.00 rate card. | Multi-model workflows permitted. |
| **`INELIGIBLE_PAID`** | Account has credit card or active Developer Plan attached. | **PERMANENTLY BLOCKED**; rejected to prevent billing. |
| **`BLOCKED_EXTERNAL`** | Missing operator credentials, opt-in, or network connectivity. | Fails closed with zero network traffic dispatched. |

---

## 3. Mandatory Operator Console Audit Checklist

Before executing the live smoke test script (`scripts/run_groq_smoke_secure.ps1`), the operator must complete the following manual checks:

```
[ ] Step 1: Open https://console.groq.com and log in.
[ ] Step 2: Navigate to Settings > Billing.
            CONFIRM: "No payment method added".
            CONFIRM: Current Plan displays "Free Plan".
            CONFIRM: No auto-reload or credit balance is active.
[ ] Step 3: Navigate to Settings > Limits.
            CONFIRM: Quotas for openai/gpt-oss-120b:
                     - Requests per minute (RPM): 30
                     - Requests per day (RPD): 1,000
                     - Tokens per minute (TPM): 8,000
                     - Tokens per day (TPD): 200,000
            CONFIRM: Quotas for openai/gpt-oss-20b:
                     - Requests per minute (RPM): 30
                     - Requests per day (RPD): 1,000
                     - Tokens per minute (TPM): 8,000
                     - Tokens per day (TPD): 200,000
[ ] Step 4: Navigate to Settings > Data Controls.
            NOTE: Observe Zero Data Retention (ZDR) toggle status.
[ ] Step 5: Navigate to API Keys.
            GENERATE: A dedicated API key for PromptIQ testing.
```

> [!CAUTION]
> If any credit card is listed under Billing, or if the plan says "Developer", **DO NOT PROCEED**. The account is `INELIGIBLE_PAID`.

---

## 4. Current Status for Phase 3.4.2

- **Operator Attestation**: PENDING
- **Dashboard Evidence**: PENDING OPERATOR INSPECTION
- **Credentials Configured**: `False`
- **Execution Safety**: 100% fail-closed (`BLOCKED_EXTERNAL`) until operator executes launcher locally outside of chat.
