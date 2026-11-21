# Live Groq GPT-OSS 20B Execution Record (Phase 3.4.2)
## Fast Critic Specialist Smoke Test Ledger, Request Metadata, and Execution Audit

**Audit Date**: 2026-11-22  
**Target Model**: `openai/gpt-oss-20b`  
**Provider**: GroqCloud (`https://api.groq.com/openai/v1/chat/completions`)  
**Assigned Logical Role**: `CRITIC` / Fast Reasoning Specialist  
**Current Execution State**: `BLOCKED_EXTERNAL` (Waiting for Operator Credential Entry via Secure Script)  

---

## 1. Test Specification & Dispatch Envelope

The smoke test for the secondary model is independently configured:

- **Endpoint**: `POST https://api.groq.com/openai/v1/chat/completions`
- **Model Identifier**: `openai/gpt-oss-20b`
- **Temperature**: `0.0`
- **Max Tokens**: `128`
- **Synthetic Prompt**:
  ```
  Return valid JSON with three fields: greeting, result, and model_role. Set greeting to Hello, result to 437, and model_role to critic. Use 19 multiplied by 23 for the calculation.
  ```
- **Expected Response Body Structure**:
  ```json
  {
    "greeting": "Hello",
    "result": 437,
    "model_role": "critic"
  }
  ```

---

## 2. In-Session Execution Verification Attempt

Executing the smoke test for Model B in the workspace produced:

```powershell
.venv\Scripts\python -m promptiq.gateway.smoke_test --provider groq --model openai/gpt-oss-20b --opt-in
```

### Actual Output:
```
============================================================
PROMPTIQ LIVE INFERENCE SMOKE TEST
Target Provider: groq
Target Model:    openai/gpt-oss-20b
Opt-In Status:   True
============================================================
{"timestamp": "2026-11-22 00:26:05,210", "level": "INFO", "logger": "promptiq", "message": "Live smoke test held: No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls."}

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
| **HTTP Request Dispatched** | **NO** | Socket held before dispatch |
| **HTTP Status Code** | `None` | Awaiting operator key |
| **Provider Request ID** | `None` | No network call executed |
| **Tokens Consumed** | `0` | Zero quota consumed |
| **Cost Incurred** | **$0.00** | Guaranteed ₹0 |
| **Mock Substitution** | **NONE** | No mock data returned |
| **Status Classification** | **`BLOCKED_EXTERNAL`** | Awaiting operator execution via `scripts/run_groq_smoke_secure.ps1` |

---

## 4. Next Step to Achieve `LIVE_VERIFIED_FREE`

Following successful verification of the 120B model, launch:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_smoke_secure.ps1 -Model "openai/gpt-oss-20b" -OptIn -ConfirmFreePlan
```
Record the genuine `x-request-id` and response payload in this ledger.
