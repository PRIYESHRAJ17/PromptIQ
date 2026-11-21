# Live Multi-Model Collaboration Execution Runbook (Phase 3.4.2)
## Operator Guide for Live Two-Model Architecture Synthesis & Adversarial Autopsy

**Target Surface**: Windows PowerShell  
**Target Provider**: GroqCloud (`https://api.groq.com/openai/v1/chat/completions`)  
**Participating Hosted Models**:
1. `openai/gpt-oss-120b` (Primary Generator & Revision Specialist)
2. `openai/gpt-oss-20b` (Adversarial Critic Specialist)
**Verified Smoke Test Status**: Both models verified HTTP 200 (`req_01m7zr9k96ethbpvc22gc1hddj` and `req_01m7zrbddcea793zn4xvrhtskw`)  

---

## 1. Security & Execution Invariants

1. **ZERO SECRETS IN CHAT OR GIT**:
   - Never paste the `GROQ_API_KEY` into chat or commits.
   - The launcher uses masked input (`Read-Host -AsSecureString`).
2. **ZERO MOCK FALLBACKS**:
   - Live execution enforces `$env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = "false"`.
   - If network or credentials fail, the pipeline fails closed with a clear error report.
3. **IMMEDIATE CREDENTIAL PURGE**:
   - The launcher disposes of BSTR buffers with `ZeroFreeBSTR` and clears environment variables in a guaranteed `finally` block.
4. **MANDATORY INVARIANT CHECK**:
   - The platform strictly enforces **NO WEBSITE FRONTEND**. Any `<html`, React, or CSS detected in candidate or revised text triggers an automatic deterministic override.

---

## 2. Command to Run

From the root of the PromptIQ repository (`c:\Users\Priyesh Raj\Desktop\PromptIQ`):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_collaboration_secure.ps1 -OptIn -ConfirmFreePlan
```

### Script Execution Parameters:
- `-OptIn`: Confirms operator authorization to send live API requests over the network.
- `-ConfirmFreePlan`: Confirms operator verified the cardless Free Plan in Groq Console (Settings > Billing: No card; Settings > Limits: Free Plan).
- `-Profile`: Optional profile (default: `STANDARD`).

---

## 3. What Happens During Execution

The script executes 5 discrete stages:

1. **Stage A (Specialist Generation)**:
   - Dispatches the complete Food Donation Platform task to `openai/gpt-oss-120b`.
   - Captures candidate architecture and genuine provider `x-request-id`.
2. **Stage B (Independent Criticism)**:
   - Dispatches candidate architecture to `openai/gpt-oss-20b`.
   - Critic performs adversarial autopsy across 10 vectors (food-safety, race conditions, RBAC, PII privacy, acceptance criteria).
   - Captures critic review and genuine provider `x-request-id`.
3. **Stage C (Candidate Deterministic Verification)**:
   - Evaluates candidate text in-memory for invariant adherence (strictly no frontend, non-empty).
4. **Stage D (Specialist Revision)**:
   - Dispatches candidate + critic autopsy back to `openai/gpt-oss-120b`.
   - Generator incorporates valid findings and explicitly documents rejected points.
   - Captures revised architecture and genuine provider `x-request-id`.
5. **Stage E (Final Deterministic Verification & Resolution Breakdown)**:
   - Evaluates revised text in-memory for invariant adherence.
   - Categorizes critic findings into `resolved`, `rejected_with_reason`, and `unresolved`.

---

## 4. Output Artifacts & Verification

Upon completion, the launcher:
1. Prints a step-by-step trace table with Step #, Role, Model ID, Request ID, HTTP status, and Latency.
2. Displays the Resolution Breakdown showing resolved, rejected, and open findings.
3. Writes the complete immutable execution record to `docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json`.
4. Outputs the mandatory diversity disclosure:
   - `is_multi_model = true`
   - `is_multi_family = false`
   - `is_multi_provider = false`
   - `model_diversity_rating = SAME_FAMILY_SAME_PROVIDER`
