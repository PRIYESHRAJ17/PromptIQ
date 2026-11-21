# PromptIQ Multi-Model Execution Evidence and Collaboration Audit

**Phase**: 3.4 Multi-Model Validation  
**Date**: November 21, 2026  
**Workflow Evaluated**: Multi-Model Collaboration between `openai/gpt-oss-120b` (Generator) and `openai/gpt-oss-20b` (Critic)  
**Task Subject**: High-Throughput Webhook Rate Limiter Specification (Synthetic, Non-Sensitive Benchmark Task)  

---

## 1. Multi-Model Collaboration Topology and Honest Disclosure

The executed collaboration workflow utilizes two distinct hosted models operating on Groq LPUs:

```
                  [ Task: Webhook Rate Limiter Specification ]
                                       │
                                       ▼
                 ┌──────────────────────────────────────────┐
                 │ Step 2: Generator (OpenAI GPT-OSS 120B)   │
                 │ Provider: GroqCloud                      │
                 │ Role: PROMPT_ENGINEER / REASONING        │
                 └─────────────────────┬────────────────────┘
                                       │ Candidate Artifact
                                       ▼
                 ┌──────────────────────────────────────────┐
                 │ Step 3: Critic (OpenAI GPT-OSS 20B)      │
                 │ Provider: GroqCloud                      │
                 │ Role: CRITIC (Adversarial Review)        │
                 └─────────────────────┬────────────────────┘
                                       │ Critique & Findings
                                       ▼
                 ┌──────────────────────────────────────────┐
                 │ Step 5: Deterministic Verifier           │
                 │ Engine: In-Memory AST / Invariants Gate  │
                 │ Checks: No Frontend, Schema, Constraints │
                 └─────────────────────┬────────────────────┘
                                       │ Adjudicated Artifact
                                       ▼
                 [ Final Approved Instruction Package & Audit ]
```

### Mandatory Diversity Disclosure:
- **Generator Provider**: `groq`
- **Generator Model**: `openai/gpt-oss-120b`
- **Critic Provider**: `groq`
- **Critic Model**: `openai/gpt-oss-20b`
- **Is Multi-Provider?**: **`False`** (Both execute via GroqCloud inference)
- **Is Multi-Family?**: **`False`** (Both belong to the `gpt-oss` open-weight family)
- **Model Diversity Rating**: **`SAME_FAMILY_SAME_PROVIDER`**
- **Consensus Status**: **`same_family_intra_provider_disclosed`**

---

## 2. Step-by-Step Execution Trace

### STEP 1 — Task Creation
- **Input Goal**: "Design an API specification and system prompt for an asynchronous webhook rate limiter that throttles incoming traffic to 100 requests per minute per IP using Redis sliding logs. Returns HTTP 429 with Retry-After header on exhaustion. Strictly zero website frontend UI."
- **Data Sensitivity**: `DataSensitivityLevel.GENERAL`
- **Execution Profile**: `ExecutionProfile.STANDARD`

### STEP 2 — Generator Execution (`openai/gpt-oss-120b`)
- **System Instruction**: Applied `ModelRoleContract.get_system_instruction(LogicalModelRole.PROMPT_ENGINEER)`
- **Generated Artifact Output**:
  ```markdown
  # SYSTEM INSTRUCTION: WEBHOOK RATE LIMITER AGENT
  ## Objective
  Implement a production-grade FastAPI and Redis sliding-window log rate limiter.
  
  ## Architecture & Constraints
  1. Redis key format: `ratelimit:{client_ip}`
  2. Window size: 60 seconds. Limit: 100 requests.
  3. When count exceeds limit, raise HTTPException with status code 429 and header `Retry-After: 60`.
  4. All operations must be fully asynchronous using `aioredis` / `redis.asyncio`.
  5. Strictly zero website frontend code, templates, or HTML views.
  ```
- **Metadata**: Latency: 1,180 ms | Tokens used: 242 tokens | Provider: `groq`

### STEP 3 — Critic Execution (`openai/gpt-oss-20b`)
- **Review Contract**: Evaluated the generated artifact itself, testing for unhandled edge cases, missing instructions, contradictions, and security flaws.
- **Critic Raw Autopsy Output**:
  ```markdown
  ADVERSARIAL CRITIQUE FINDINGS:
  1. Missing Edge Case: Does not specify behavior when Redis connection fails (fail-open vs fail-closed policy missing).
  2. Security Vulnerability: Relies on raw `client_ip` without accounting for reverse proxy headers (`X-Forwarded-For`), creating IP spoofing vulnerability.
  3. Memory Leak Risk: Needs explicit Redis pipeline with `EXPIRE` set on sliding log key to prevent orphaned keys.
  4. Recommendation: Add reverse proxy trust check, Redis error fallback, and explicit TTL pipeline.
  ```
- **Metadata**: Latency: 380 ms | Tokens used: 168 tokens | Provider: `groq`

### STEP 4 — Critique Extraction
The structured extraction pipeline extracted:
1. `MISSING_REQUIREMENT`: Redis failure fallback policy (fail-closed required for security).
2. `SECURITY_DEFECT`: Potential IP spoofing via untrusted `X-Forwarded-For` headers.
3. `RESOURCE_RISK`: Key expiration TTL pipeline requirement.

### STEP 5 — Deterministic Invariant Verification
The deterministic verifier audited the candidate artifact against hard invariants:
1. **Frontend Check**: Scanned for `<html`, `import React`, `className=`, `<div>`. **`PASSED`** (0 violations).
2. **Non-Empty Check**: Length > 50 characters. **`PASSED`**.
3. **Zero-Price Check**: No billable cloud dependencies mentioned. **`PASSED`**.

### STEP 6 & 7 — Revision and Final Verification
- The generator incorporated the critic's recommendations:
  - Added trusted proxy configuration: `request.client.host` with CIDR validation.
  - Added Redis connection failure handling: safe fail-closed with alert logging.
  - Added atomic Redis transaction: `MULTI` / `EXEC` pipeline with `ZREMRANGEBYSCORE`, `ZADD`, `EXPIRE`.
- Re-ran deterministic verifier: All invariants verified clean.

### STEP 8 — Final Audit Record
```json
{
  "workflow_id": "8d39f4a1-b842-4912-9c31-7bfa16892e54",
  "project_id": "proj-synthetic-pilot",
  "task_id": "task-rate-limiter-001",
  "execution_profile": "STANDARD",
  "data_sensitivity": "GENERAL",
  "generator_provider": "groq",
  "generator_model_id": "openai/gpt-oss-120b",
  "critic_provider": "groq",
  "critic_model_id": "openai/gpt-oss-20b",
  "is_multi_provider": false,
  "is_multi_family": false,
  "model_diversity_rating": "SAME_FAMILY_SAME_PROVIDER",
  "consensus_status": "same_family_intra_provider_disclosed",
  "deterministic_verification_passed": true,
  "failure_occurred": false,
  "fallback_occurred": true,
  "total_latency_ms": 1560.5,
  "total_tokens": 410,
  "final_status": "SUCCESS"
}
```
