# PromptIQ Model Intelligence Architecture

**Version**: 3.2.0  
**Status**: ACTIVE / PRODUCTION-READY  
**Architecture Paradigm**: Provider-Independent, Centrally Managed Multi-Model Pool with Dynamic Role Routing

---

## 1. Architectural Philosophy

PromptIQ transitions decisively away from a single-primary-model dependency to a **decentralized, multi-model intelligence pool**. No single model or provider holds a monopoly over PromptIQ's reasoning or execution pipeline.

### Core Architectural Principles:
1. **Provider Independence**: The core engine communicates via vendor-neutral PromptIQ Prompt Specifications (PPS). Upstream model providers are interchangeable adapters.
2. **Specialized Logical Roles**: Workflows decompose tasks across distinct functional roles (Orchestrator, Reasoning, Fast, Research, Prompt Engineer, Critic, Verifier).
3. **Independent Adversarial Critique**: The Critic role is structurally decoupled from the generator model family (e.g. if a Llama model generates, a Gemini or Qwen model critiques).
4. **Strict Fail-Closed Zero-Price**: Every model in the active pool is guaranteed $0/token. When free-tier quotas are exhausted, operations pause safely without fallback to paid routes.
5. **Data Privacy-Aware Routing**: Tasks with `CONFIDENTIAL` or `RESTRICTED` sensitivity are blocked from routes where provider terms permit human review or model training.

---

## 2. Logical Model Roles

PromptIQ defines 7 specialized functional model roles:

```
                          ┌───────────────────────────┐
                          │    ORCHESTRATOR MODEL     │
                          │   (Workflow Coordination) │
                          └─────────────┬─────────────┘
                                        │
        ┌───────────────────────┬───────┴───────────────┬───────────────────────┐
        ▼                       ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  FAST MODEL   │       │REASONING MODEL│       │RESEARCH MODEL │       │PROMPT ENGINEER│
│(Classification│       │ (Architecture │       │  (Evidence    │       │ (Native Target│
│  & Extraction)│       │ & Trade-offs) │       │   Synthesis)  │       │  Compilation) │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │                       │
        └───────────────────────┼───────────────────────┴───────────────────────┘
                                ▼
                    ┌───────────────────────────┐
                    │  INDEPENDENT CRITIC MODEL │
                    │(Adversarial Autopsy / Diff│
                    │   Alternative Family)     │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │    VERIFICATION ENGINE    │
                    │ (Deterministic Invariant  │
                    │   & Schema Enforcement)   │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │  FINAL CONSOLIDATION &    │
                    │   AUDIT RECORD LOGGING    │
                    └───────────────────────────┘
```

### Role Specifications:
1. **Orchestrator Model**: Decomposes user goals, assigns subtasks to specialist models, oversees disagreement resolution, and consolidates the final specification.
2. **Reasoning Model**: Analyzes complex constraints, resolves multi-dimensional architectural trade-offs, and detects subtle logical contradictions.
3. **Fast Model**: Low-latency sub-second extraction, entity classification, and quick discovery turns.
4. **Research Model**: Formulates structured search queries, analyzes external source veracity, and maps claims into the Evidence Ledger.
5. **Prompt Engineering Model**: Structures instruction hierarchies, applies target-native syntax conventions (Antigravity, Claude Code, Cursor, Codex, Gemini CLI), and optimizes context budgets.
6. **Independent Critic Model**: Conducts unsparing adversarial autopsies, searches for security loopholes, and exposes missing requirements. **Mandatory constraint: MUST be an alternative model family from the generating model.**
7. **Verification Model / Engine**: Deterministically validates JSON schemas, checks boundary conditions, and enforces core invariants (Strictly No Website Frontend, Zero-Price).

---

## 3. Dynamic Model Router

The `DynamicModelRouter` dynamically routes requests based on multi-dimensional criteria:

$$\text{Eligibility} = \text{RoleMatch} \land \text{ContextFit} \land \text{PrivacySafe} \land \text{QuotaAvailable} \land \text{FamilySeparation}$$

1. **Role Capability Match**: Verifies model capabilities (`reasoning`, `tools`, `structured_output`, `vision`, `long_context`).
2. **Data Sensitivity Level**:
   - `PUBLIC`: All verified zero-price models.
   - `GENERAL`: Google, Groq, OpenRouter :free, Mock.
   - `CONFIDENTIAL`: Groq, Mock (rejects Google Developer API free tier due to human data review terms).
   - `RESTRICTED`: Internal zero-retention mock only.
3. **Capacity Governor Check**: Inspects sliding-window RPM, RPD, TPM, TPD and upstream HTTP response headers (`retry-after`, `x-ratelimit-*`).
4. **Family Separation Constraint**: Ensures `Critic.family != Generator.family`.

---

## 4. Multi-Model Collaboration Profiles

| Profile | Pipeline Flow | Latency Target | Best For |
| :--- | :--- | :--- | :--- |
| **QUICK** | Fast Model $\rightarrow$ Deterministic Verifier $\rightarrow$ Consolidate | $<1.5\text{ s}$ | Classification, quick discovery turns, parameter extraction |
| **STANDARD** | Orchestrator $\rightarrow$ Prompt Engineer $\rightarrow$ Independent Critic $\rightarrow$ Deterministic Verifier $\rightarrow$ Consolidate | $2.5\text{–}4.0\text{ s}$ | Standard target compilation, requirements drafting, routine prompts |
| **DEEP** | Orchestrator $\rightarrow$ Reasoning Model $\rightarrow$ Prompt Engineer $\rightarrow$ Independent Critic $\rightarrow$ Verifier $\rightarrow$ Consolidate | $4.0\text{–}8.0\text{ s}$ | Complex architectures, multi-tenant security specifications, system design |
| **HIGH_RISK** | Orchestrator $\rightarrow$ 2 Independent Generators $\rightarrow$ Adversarial Critic $\rightarrow$ Verifier $\rightarrow$ Consensus Adjudication | $6.0\text{–}12.0\text{ s}$ | Safety-critical logic, financial calculations, zero-trust infrastructure |
