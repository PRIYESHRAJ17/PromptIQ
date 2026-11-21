# PromptIQ Live Hosted Inference Verification Ledger

**Phase**: 3.4 — First Live AI Execution, Multi-Model Validation and Cloud Runtime Proof  
**Audit Date**: November 21, 2026  
**Auditor**: Model Operations & Live Systems Verification Group  
**Verification Standard**: Never manufacture live scores. If external credentials are absent, report `BLOCKED_EXTERNAL` or `UNVERIFIED`.

---

## 1. Live Inference Verification Summary

| Provider Route | Model Identifier | Free Plan Quotas | Operator Credential Status | Opt-In Status | Live Verification Result | Evidence & Action Required |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **GroqCloud Free Tier** | `openai/gpt-oss-120b` | 30 RPM / 1,000 RPD / 8k TPM / 100k TPD | **UNCONFIGURED** | Opt-In Gate Active | **`BLOCKED_EXTERNAL`** | Smoke test utility verified: returns `BLOCKED_EXTERNAL` with clear notice when `OPERATOR_GROQ_API_KEY` is not present. |
| **GroqCloud Free Tier** | `openai/gpt-oss-20b` | 30 RPM / 14,400 RPD / 6k TPM / 500k TPD | **UNCONFIGURED** | Opt-In Gate Active | **`BLOCKED_EXTERNAL`** | Smoke test utility verified: returns `BLOCKED_EXTERNAL`. |
| **Google AI Studio** | `gemini-3.8-flash` | 15 RPM / 1,500 RPD / 1M TPM | **UNCONFIGURED** | Opt-In Gate Active | **`CONDITIONALLY_ELIGIBLE` / `BLOCKED_EXTERNAL`** | Excluded from general production due to terms barring minor audiences (<18) and free-tier prompt training. |
| **Google AI Studio** | `gemini-3.5-flash-lite`| 30 RPM / 1,500 RPD / 1M TPM | **UNCONFIGURED** | Opt-In Gate Active | **`CONDITIONALLY_ELIGIBLE` / `BLOCKED_EXTERNAL`** | Conditional on adult-only developer environment. |
| **Internal Deterministic**| `promptiq-mock-v1` | Unlimited / In-Memory | **ACTIVE** | Automated | **`VERIFIED`** | Fully executed and verified across 85 automated tests. Safe for air-gapped RESTRICTED compliance data. |

---

## 2. Safe Live Smoke-Test Protocol (`promptiq/gateway/smoke_test.py`)

To verify live hosted inference without risking unexpected token consumption or exposing keys:

1. **Mandatory Opt-In Gate**:
   Network calls cannot be made during standard test suites or builds. Execution requires explicit opt-in:
   ```bash
   python -m promptiq.gateway.smoke_test --opt-in --provider groq --model openai/gpt-oss-120b
   ```
2. **Account Attestation Pre-Check**:
   `OperatorAccountVerifier.verify_operator_account()` checks that the account is attested on the Free Plan, with no billing card attached, and that the provider hard-stops with HTTP 429 when quota is exhausted.
3. **Absence of Credentials Behavior**:
   When no operator key is injected, the smoke test safely terminates and outputs:
   ```json
   {
     "status": "BLOCKED_EXTERNAL",
     "provider": "groq",
     "model_id": "openai/gpt-oss-120b",
     "http_status": null,
     "success": false,
     "error": "No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls.",
     "notice": "Never substitute mock execution for live verification. Real operator credentials and opt-in required."
   }
   ```
4. **Zero Silent Fallbacks**:
   Mock adapters are strictly decoupled from live adapters. If a live adapter is called without credentials in live mode, it raises `CapacityExhaustedError` rather than silently disguising missing credentials as mock execution.
