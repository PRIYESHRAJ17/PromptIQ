# PromptIQ Multi-Model Live Test Plan
## Empirical Evaluation Protocol for Multi-Model Intelligence and Zero-Spend Inference

**Revision**: 2026.11-v3.3  
**Date**: November 21, 2026  
**Auditor**: Model Tournament & Verification Engineering Board  

---

## 1. Test Configurations

The live test protocol evaluates four distinct collaboration topologies across real-world PromptIQ workloads:

### Configuration A: True Multi-Provider (General / Public Data, Adult Audience)
- **Primary Generator**: `openai/gpt-oss-120b` (GroqCloud)
- **Independent Critic**: `gemini-3.8-flash` (Google AI Studio)
- **Verifier & Code Formatter**: `qwen/qwen3.8-27b` (GroqCloud)
- **Objective**: Measure diversity of critique, cross-model instruction adherence, and hallucination reduction.

### Configuration B: Confidential Data (Intra-Provider Multi-Family)
- **Primary Generator**: `openai/gpt-oss-120b` (GroqCloud)
- **Independent Critic**: `qwen/qwen3.8-27b` (GroqCloud)
- **Fast Filter**: `openai/gpt-oss-20b` (GroqCloud)
- **Objective**: Verify that confidential tasks complete with zero training risk, evaluating the difference in critique sharpness compared to cross-provider.

### Configuration C: Edge Proxy / Low Latency (Fast Filter Routing)
- **Edge Classifier**: `@cf/meta/llama-3.1-8b-instruct` (Cloudflare Workers AI)
- **Orchestrator**: `gemini-3.5-flash-lite` (Google AI Studio)
- **Objective**: Benchmark edge routing latency and daily Neuron quota tracking.

### Configuration D: Air-Gapped Internal (Restricted Data)
- **Engine**: `promptiq-mock-v1` (Internal Deterministic)
- **Objective**: Verify that sensitive compliance data executes with zero external egress, deterministic invariant guarantees, and sub-5ms latency.

---

## 2. Blind Evaluation Methodology

To prevent model bias or decorative evaluation:
1. **Anonymized Output Comparison**:
   - The test harness strips model identifiers and metadata from generated prompts and autopsy reports.
   - Evaluator prompts receive Candidate 1 and Candidate 2 in randomized order.
2. **Deterministic Evaluation Dimensions**:
   - **Instruction Adherence (0.0 - 1.0)**: Strict checking of mandatory tags, XML wrappers, role definitions, and negative constraints.
   - **JSON Schema Strictness (0.0 - 1.0)**: Validation using Pydantic schema deserialization. Non-conforming JSON receives a 0.0 score.
   - **Flaw Detection Accuracy (0.0 - 1.0)**: Seeded adversarial prompts containing known vulnerabilities (e.g. prompt injection, context leakage, infinite loops) must be flagged by the critic.
   - **Latency (ms)**: Measured from HTTP socket write to last byte received.
   - **Token Consumption**: Actual input and output tokens billed against provider daily quota buckets.

---

## 3. Live Execution Protocol & Disclosure Rules

### Protocol for Operator Credential Injection:
When the operator is ready to execute live evaluation:
1. The operator injects server-side environment variables:
   - `OPERATOR_GEMINI_API_KEY`
   - `OPERATOR_GROQ_API_KEY`
2. The operator runs the live benchmark suite:
   ```bash
   python -m promptiq.eval.tournament --live --rounds 5
   ```
3. The harness records live HTTP roundtrips, response headers, `x-ratelimit-remaining`, and latency.

### Strict Prohibition of Manufactured Metrics:
In the absence of live operator credentials:
- The system **must disclose** `status = "UNVERIFIED (Awaiting operator credentials)"`.
- The sample size **must be 0**.
- Benchmark scores **must not be populated with fake numbers**.
- The system must explicitly report: *"Scores are unverified pending live execution with server-side keys."*
