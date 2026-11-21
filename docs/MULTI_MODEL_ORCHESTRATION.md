# PromptIQ Multi-Model Orchestration & Collaboration Specification

**Version**: 3.2.0  
**Engine**: `MultiModelCollaborationPipeline` (`promptiq.orchestrator.collaboration`)  
**Status**: ACTIVE / PRODUCTION-VERIFIED  

---

## 1. The Six-Step Collaboration Workflow

PromptIQ executes intelligent tasks through a formal six-step multi-model collaboration pipeline:

```
Step 1: Task Analysis & Planning (Orchestrator Model)
                      │
                      ▼
Step 2: Specialist Generation (Prompt Engineer / Reasoning / Fast)
                      │
                      ▼
Step 3: Independent Evaluation & Critique (Critic Model - Alternative Family)
                      │
                      ▼
Step 4: Deterministic Verification (Invariant & Schema Engine)
                      │
                      ▼
Step 5: Disagreement Resolution (Adjudication / Uncertainty Retention)
                      │
                      ▼
Step 6: Final Consolidation & Audit Record Generation
```

### Detailed Step Analysis:

1. **Step 1: Task Analysis & Role Planning**:
   - The Orchestrator analyzes user intent, determines the execution profile (`QUICK`, `STANDARD`, `DEEP`, `HIGH_RISK`), checks data sensitivity, and plans required sub-tasks.
2. **Step 2: Specialist Generation**:
   - The selected specialist model (e.g. Prompt Engineering Model for target compilation, Fast Model for intake classification) generates the candidate artifact.
   - Under `HIGH_RISK` profile, two independent generators from different model families produce parallel drafts.
3. **Step 3: Independent Evaluation & Critique**:
   - The Independent Critic model conducts an adversarial prompt autopsy.
   - Inspects for missing edge cases, instruction ambiguities, security bypasses, and feasibility flaws.
   - **Enforces structural family independence** ($M_{\text{critic}} \neq M_{\text{gen}}$).
4. **Step 4: Deterministic Verification**:
   - Executes deterministic rule engines:
     - Invariant: Strictly No Website Frontend (blocks React/Next.js/HTML/CSS).
     - Invariant: Zero-Price $0/token (verifies no paid billing assumptions).
     - Validates pure JSON output schemas and boundary conditions.
5. **Step 5: Disagreement Resolution**:
   - If deterministic invariants are violated: **`deterministic_override`** cleanses or blocks the artifact.
   - If the Critic raises architectural or ambiguity concerns:
     - Under `STANDARD` or `DEEP` profiles: **`adjudicated`** incorporating critique corrections.
     - Under quick turns: **`uncertainty_retained`** annotating caveats in the audit ledger.
6. **Step 6: Final Consolidation & Audit Record**:
   - The Orchestrator synthesizes the verified specification.
   - Generates an immutable `MultiModelExecutionAuditRecord` recording latency, tokens, providers, and consensus metrics.

---

## 2. Multi-Model Execution Audit Record Schema

Every collaboration session records an audit log containing:
- `workflow_id`: Unique execution identifier
- `project_id`: Scoped project identifier
- `task_id`: Task identifier
- `execution_profile`: `QUICK`, `STANDARD`, `DEEP`, or `HIGH_RISK`
- `data_sensitivity`: `PUBLIC`, `GENERAL`, `CONFIDENTIAL`, or `RESTRICTED`
- `steps`: List of `ExecutionStepRecord` items (role, provider, model_id, timestamp, latency_ms, input_tokens, output_tokens, verification_passed, findings)
- `consensus_status`: `agreed`, `adjudicated`, `uncertainty_retained`, `deterministic_override`
- `total_latency_ms`: End-to-end wall-clock latency
- `total_tokens`: Cumulative token count
- `final_status`: `SUCCESS` or `FAILED`
