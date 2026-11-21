# Secure Windows Credential Runbook (Phase 3.4.2)
## Local In-Memory Credential Injection and Live Smoke Test Protocol

**Document Version**: 1.0  
**Target Environment**: Windows PowerShell (Desktop Workstation)  
**Security Level**: High (Zero Secret Leakage Invariant)  

---

## 1. Absolute Credential Invariant

> [!CAUTION]
> **NEVER paste an API key into chat.**
> Doing so permanently embeds the secret in conversation logs and model training transcripts. 
> PromptIQ strictly enforces local, in-memory credential injection.

---

## 2. In-Memory PowerShell Security Architecture

The secure launcher script at `scripts/run_groq_smoke_secure.ps1` implements the following security pipeline:

1. **Hidden Input**: Uses `Read-Host -AsSecureString` so key characters are never displayed or stored in shell history.
2. **In-Memory BSTR Unmarshaling**: Converts the SecureString into a plain-text BSTR pointer in process RAM, assigns it to the child process environment (`$env:GROQ_API_KEY`), and immediately zeroes the BSTR buffer using `[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)`.
3. **Zero Disk Writes**: No `.env` file is generated, modified, or read.
4. **No CLI Arguments**: The key is never passed via command-line arguments (preventing exposure via Task Manager or `Get-Process`).
5. **Immediate Environment Purge**: A PowerShell `finally` block nullifies `$env:GROQ_API_KEY` and triggers garbage collection immediately upon process exit.

> [!NOTE]
> **Process Scope Boundary**: Process environment variables are accessible to other processes running under the same Windows user session. This mechanism prevents accidental disk persistence and Git leakage, but does not isolate against local malware running under your user context.

---

## 3. Step-by-Step Operator Runbook

Open a standard Windows PowerShell window in the PromptIQ repository root:

```powershell
cd "c:\Users\Priyesh Raj\Desktop\PromptIQ"
```

### Test 1: Primary Generator (`openai/gpt-oss-120b`)
Run the secure launcher with explicit opt-in and free plan attestation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_smoke_secure.ps1 -Model "openai/gpt-oss-120b" -OptIn -ConfirmFreePlan
```

When prompted:
```
Please enter your Groq API key.
(Input is masked and will be stored strictly in memory for this session run)
Groq API Key: ****************************************************
```
Type or paste your Groq API key (`gsk_...`) and press **Enter**.

### Expected Console Output on Success:
```
Executing isolated smoke test...
============================================================
PROMPTIQ LIVE INFERENCE SMOKE TEST
Target Provider: groq
Target Model:    openai/gpt-oss-120b
Opt-In Status:   True
============================================================

Execution Result: LIVE_VERIFIED_FREE
Success:          True
HTTP Status:      200
Request ID:       req_01j...
Req Timestamp:    2026-11-22T...
Resp Timestamp:   2026-11-22T...
Latency:          720.5 ms
Tokens Used:      42 (Prompt: 32, Completion: 10)
Rate Limits Rem:  Requests: 999, Tokens: 7968
Account State:    DASHBOARD_EVIDENCED
Response Text:    {"greeting": "Hello", "result": 437, "model_role": "generator"}
============================================================

[SECURITY] Environment variables and in-memory credential buffers cleared.
```

---

### Test 2: Fast Critic Specialist (`openai/gpt-oss-20b`)
Run the launcher for the 20B model:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_smoke_secure.ps1 -Model "openai/gpt-oss-20b" -OptIn -ConfirmFreePlan
```

Expected Response:
```
Execution Result: LIVE_VERIFIED_FREE
Success:          True
HTTP Status:      200
Response Text:    {"greeting": "Hello", "result": 437, "model_role": "critic"}
```

---

## 4. Failure and Quota Exhaustion Behaviors

| Scenario | CLI Status | Action to Take |
|---|---|---|
| **No Key Entered** | `[ERROR] No API key entered` | Script halts before opening socket. |
| **Missing Flags** | `[ERROR] Missing mandatory -OptIn flag` | Script halts before prompting for key. |
| **Invalid Key** | `PROVIDER_HTTP_ERROR (HTTP 401)` | Check key validity in console; no retries executed. |
| **Rate Limit Hit** | `QUOTA_EXHAUSTED (HTTP 429)` | Native hard stop confirmed; wait 60s for sliding window reset. |
