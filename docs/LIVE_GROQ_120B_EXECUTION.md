# Live Groq GPT-OSS 120B Execution Record (Phase 3.4.2)
## Primary Generator Smoke Test Ledger, Request Metadata, and Execution Audit

**Audit Date**: 2026-11-22  
**Target Model**: `openai/gpt-oss-120b`  
**Provider**: GroqCloud (`https://api.groq.com/openai/v1/chat/completions`)  
**Assigned Logical Role**: `PROMPT_ENGINEER` / Primary Reasoning  
**Current Execution State**: `BLOCKED_EXTERNAL` (Waiting for Operator Credential Entry via Secure Script)  

---

## 1. Test Specification & Dispatch Envelope

The smoke test utility is prepared to dispatch a minimal, deterministic synthetic payload:

- **Endpoint**: `POST https://api.groq.com/openai/v1/chat/completions`
- **Model Identifier**: `openai/gpt-oss-120b`
- **Temperature**: `0.0`
- **Max Tokens**: `128` (Strictly bounded to prevent TPM exhaustion)
- **Synthetic Prompt**:
  ```
  Return valid JSON with three fields: greeting, result, and model_role. Set greeting to Hello, result to 437, and model_role to generator. Use 19 multiplied by 23 for the calculation.
  ```
- **Expected Response Body Structure**:
  ```json
  {
    "greeting": "Hello",
    "result": 437,
    "model_role": "generator"
  }
  ```

---

## 2. In-Session Execution Verification Attempt

Executing the smoke test in the agent workspace produced the following immutable execution log:

```powershell
.venv\Scripts\python -m promptiq.gateway.smoke_test --provider groq --model openai/gpt-oss-120b --opt-in
```

### Actual Output:
```
============================================================
PROMPTIQ LIVE INFERENCE SMOKE TEST
Target Provider: groq
Target Model:    openai/gpt-oss-120b
Opt-In Status:   True
============================================================
{"timestamp": "2026-11-22 00:26:04,110", "level": "INFO", "logger": "promptiq", "message": "Live smoke test held: No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls."}

Execution Result: BLOCKED_EXTERNAL
Success:          False
Error / Hold:     No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls.
Notice:           Never substitute mock execution for live verification. Real operator credentials and opt-in required.
============================================================
```

---

## 3. Forensic Ledger Entry

| Metric / Parameter | Value / State | Verification Note |
|---|---|---|
| **HTTP Request Dispatched** | **NO** | Socket held before dispatch to prevent unauthenticated network traffic |
| **HTTP Status Code** | `None` | Awaiting operator key |
| **Provider Request ID** | `None` | No provider interaction took place |
| **Tokens Consumed** | `0` | Zero quota consumed |
| **Cost Incurred** | **$0.00** | Guaranteed ₹0 |
| **Mock Substitution** | **NONE** | No mock data returned; fail-closed enforcement active |
| **Status Classification** | **`BLOCKED_EXTERNAL`** | Awaiting operator execution via `scripts/run_groq_smoke_secure.ps1` |

---

## 4. Next Step to Achieve `LIVE_VERIFIED_FREE`

The operator must launch:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_smoke_secure.ps1 -Model "openai/gpt-oss-120b" -OptIn -ConfirmFreePlan
```
Once run locally, the script outputs the genuine `x-request-id`, latency, and rate-limit headers to be recorded in this ledger.
