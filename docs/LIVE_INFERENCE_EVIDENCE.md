# Live Inference Evidence & Operator Runbook (Phase 3.4.1)
## Verification Ledger, Credential Security, and Live Smoke Test Protocol

**Audit Date**: 2026-11-22  
**Status**: `BLOCKED_EXTERNAL` (Credentials Not Configured in Current Session)  
**Security Level**: High (Zero Secret Leakage Guaranteed)  

---

## 1. Operator Credential Security Invariants

In strict adherence to PromptIQ invariants:
1. **Never in Chat**: The user/operator must **never** paste an API key into chat conversations.
2. **Never in Git**: All `.env` files are excluded by `.gitignore`. No hardcoded strings exist in source files.
3. **No Silent Mocking**: When credentials are not configured, the inference engine strictly fails closed with `BLOCKED_EXTERNAL` or `CapacityExhaustedError`. It **never** fabricates a fake HTTP 200 or replaces real calls with mock data.
4. **No Header Leakage**: Authorization headers and Bearer tokens are redacted at all logging levels (SEC-023).

---

## 2. Live Smoke Test Execution Record (Current Session)

The smoke test CLI was executed in the workspace using the following command:

```powershell
.venv\Scripts\python -m promptiq.gateway.smoke_test --provider groq --opt-in
```

### Actual Output Captured:
```
============================================================
PROMPTIQ LIVE INFERENCE SMOKE TEST
Target Provider: groq
Target Model:    openai/gpt-oss-120b
Opt-In Status:   True
============================================================
{"timestamp": "2026-11-22 00:07:57,020", "level": "INFO", "logger": "promptiq", "message": "Live smoke test held: No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls.", "extra": {"taskName": "Task-1"}}

Execution Result: BLOCKED_EXTERNAL
Success:          False
Error / Hold:     No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls.
Notice:           Never substitute mock execution for live verification. Real operator credentials and opt-in required.
============================================================
```

### Forensic Ledger Entry:
- **Timestamp**: `2026-11-22T00:07:57.020+05:30`
- **Target Provider**: `groq`
- **Target Model**: `openai/gpt-oss-120b`
- **HTTP Request Sent**: **NO** (Dispatched halted before socket creation due to missing credentials)
- **HTTP Status Received**: `None`
- **Provider Request ID**: `None`
- **Cost Incurred**: **$0.00**
- **Classification**: **`BLOCKED_EXTERNAL`**
- **Verdict**: Fail-closed mechanism operated perfectly as designed. No mock data was returned.

---

## 3. Operator Windows Runbook for Live Execution

When the operator decides to perform live inference testing on their local machine, they must follow these secure steps outside the chat:

### Step 1: Confirm Cardless Free Tier in Groq Console
1. Log in to [https://console.groq.com](https://console.groq.com).
2. Go to **Settings > Billing**: Confirm **No credit card** is on file.
3. Go to **Settings > Limits**: Confirm **Free Plan** is active (1,000 RPD for GPT-OSS).
4. Go to **API Keys**: Generate a dedicated key for PromptIQ testing.

### Step 2: Configure Environment Variables in Windows PowerShell
Open your local PowerShell window (do not share output in chat):

```powershell
# Set operator API key in session memory only (will not persist to disk)
$env:GROQ_API_KEY="gsk_your_groq_api_key_here"

# Attest that you verified cardless free plan in the dashboard
$env:PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED="true"
```

*For Command Prompt (CMD)*:
```cmd
set GROQ_API_KEY=gsk_your_groq_api_key_here
set PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED=true
```

### Step 3: Run the Safe Smoke Test CLI
Execute the single-request test with explicit opt-in:

```powershell
# Test Primary Generator (openai/gpt-oss-120b)
python -m promptiq.gateway.smoke_test --provider groq --model openai/gpt-oss-120b --opt-in

# Test Fast Critic Specialist (openai/gpt-oss-20b)
python -m promptiq.gateway.smoke_test --provider groq --model openai/gpt-oss-20b --opt-in
```

### Step 4: Verification Checklist Upon Execution
A successful live test will print:
- `Execution Result: SUCCESS`
- `Provider: groq`
- `Model: openai/gpt-oss-120b` (or `openai/gpt-oss-20b`)
- `Provider Request ID: <actual-uuid-from-groq>`
- `Latency (ms): <actual-network-roundtrip>`
- `Tokens: prompt_tokens: ..., completion_tokens: ...`
- `Cost: $0.00 (Confirmed under Groq Free Plan)`

If any limit is hit or billing is detected, the runbook instructs immediate termination.
