# PromptIQ Multi-Model Availability Report
## Architectural Role Separation, Provider Independence, and Fallback Disclosures

**Revision**: 2026.11-v3.3  
**Date**: November 21, 2026  
**Auditor**: Multi-Model Architecture & Orchestration Group  

---

## 1. Multi-Model Role Matrix

PromptIQ defines seven distinct logical model roles. Each role is mapped to an eligible zero-price model family to maximize reasoning quality, execution speed, and token conservation:

| Logical Model Role | Primary Verified Candidate | Backup Verified Candidate | Context Req. | Capabilities Required | Selection Rationale |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **`ORCHESTRATOR`** | `gemini-3.8-flash` (Google) | `openai/gpt-oss-120b` (Groq) | 1M | Tool use, large context, workflow management | High context allows managing extensive conversation history and multi-file project specifications. |
| **`REASONING`** | `openai/gpt-oss-120b` (Groq) | `gemini-3.8-flash` (Google) | 128k | Complex logic, step-by-step reasoning, AST analysis | Deep reasoning capabilities on LPUs with zero model training. |
| **`FAST`** | `gemini-3.5-flash-lite` (Google) | `openai/gpt-oss-20b` (Groq) | 128k | High RPM, low latency, token filtering | Conserves daily token budget by executing routine classification in sub-second time. |
| **`RESEARCH`** | `gemini-3.8-flash` (Google) | `openai/gpt-oss-120b` (Groq) | 1M | Long context, document synthesis, evidence tracing | Long context enables reading complete technical documentation without truncation. |
| **`PROMPT_ENGINEER`**| `openai/gpt-oss-120b` (Groq) | `gemini-3.8-flash` (Google) | 128k | Structured prompt compilation, target adapter schemas | Expert at compiling precise target-native system prompts (Antigravity, Claude Code, Cursor). |
| **`CRITIC`** | `openai/gpt-oss-120b` (Groq) | `qwen/qwen3.8-27b` (Groq) | 128k | Adversarial audit, autopsy analysis, flaw detection | **Must be independent of generator family.** Cannot review its own output without disclosure. |
| **`VERIFIER`** | `qwen/qwen3.8-27b` (Groq) | `promptiq-mock-v1` (Internal) | 128k | Syntax verification, schema compliance, deterministic tests | Specialized coding model checks syntax, JSON schemas, and structural boundaries. |

---

## 2. Independence Hierarchy: Multi-Provider vs Multi-Family vs Intra-Provider

PromptIQ strictly distinguishes between three tiers of model diversity:

```
Tier 1: True Multi-Provider Independence
[ Google AI Studio (Gemini 3.8 Flash) ] ── Generator
[ GroqCloud (OpenAI GPT-OSS 120B) ]      ── Independent Critic
Outcome: Maximum diversity. Different weights, different host, different training data, different infrastructure.

Tier 2: Multi-Family, Single-Provider Independence (Used for CONFIDENTIAL data)
[ GroqCloud (OpenAI GPT-OSS 120B) ]      ── Generator
[ GroqCloud (Qwen 3.8 27B) ]             ── Independent Critic
Outcome: High architectural diversity. Different weights, different model families, shared inference host.
Governance Action: Mandatory disclosure (consensus_status = "single_provider_disclosed").

Tier 3: Same-Model Self-Review (PROHIBITED)
[ GroqCloud (OpenAI GPT-OSS 120B) ]      ── Generator
[ GroqCloud (OpenAI GPT-OSS 120B) ]      ── Critic
Outcome: High correlation of blind spots and bias.
Governance Action: Rejected by DynamicModelRouter (exclude_families parameter prevents same family).
```

---

## 3. Consensus and Adjudication Architecture

When multiple models collaborate on a prompt autopsy or specification design:

1. **Generation Phase**:
   - The primary generator (e.g. `openai/gpt-oss-120b`) produces candidate artifacts and system instructions.
2. **Adversarial Critique Phase**:
   - The critic model (e.g. `gemini-3.8-flash` or `qwen/qwen3.8-27b`) audits the generation without seeing prior self-assessments.
   - The critic outputs structured findings: `HIGH_RISK`, `MEDIUM_RISK`, `LOW_RISK`.
3. **Consensus Determination**:
   - If critic identifies zero high-severity flaws: `consensus_status = "agreed"`.
   - If critic identifies critical flaws and generator amends: `consensus_status = "adjudicated"`.
   - If critic persistently rejects and generator cannot resolve: `consensus_status = "critic_failed"`, execution fails closed (`final_status = "FAILED"`).
   - If only a single provider was available (due to data confidentiality or regional outages): `consensus_status = "single_provider_disclosed"`.
