# PROMPTIQ V6 — INTELLIGENCE ARCHITECTURE SPECIFICATION

## Executive Overview

PromptIQ V6 delivers an evidence-driven, epistemically calibrated intelligence and reasoning engine that replaces shallow prompt transformations with structured requirement decomposition, information sufficiency evaluation, conflict-aware Project Constitutions, and target-native prompt compilation.

---

## 1. Intent & Requirement Decomposition Engine

**Implementation Source**: `promptiq/intelligence/intent.py` (`IntentReasoningEngine`)

### Capabilities & Contracts
1. **Hierarchical Objective Analysis**:
   - Classifies primary goals vs secondary supporting objectives.
   - Categorizes requirements by provenance:
     - `EXPLICIT_PROVIDED`: Extracted verbatim or directly stated by user.
     - `STRONGLY_IMPLIED`: Inferred from domain norms (e.g. CSRF protection in web APIs).
     - `DOMAIN_DEFAULT`: Standard platform defaults.
     - `RESEARCH_BACKED`: Sourced from external documentation or standards.
     - `UNKNOWN_AMBIGUOUS`: Flagged for clarifying questions.
2. **Impact & Invariant Classification**:
   - Assesses requirement impact as `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
   - Identifies non-negotiable boundaries (e.g. `zero_price_enforcement`, `strictly_no_frontend`, `least_privilege`).

---

## 2. Epistemic Uncertainty & Calibrated Claim Tracking

**Implementation Source**: `promptiq/intelligence/uncertainty.py` (`UncertaintyTracker`, `CalibratedClaim`)

### Epistemic Status Hierarchy
Claims, facts, and assertions within PromptIQ track an explicit epistemic status:
- `VERIFIED_FACT`: Established by deterministic code, cryptographic hash, or primary database check.
- `SOURCE_SUPPORTED_CLAIM`: Grounded in authoritative secondary sources with character-offset citations.
- `MODEL_INTERPRETATION`: Derived from LLM reasoning; requires evaluation before acceptance.
- `INFERENCE`: Deductive or inductive conclusion drawn from existing premises.
- `ASSUMPTION`: Working hypothesis explicitly declared to avoid unstated assumptions.
- `CONTRADICTORY_CLAIM`: Competing assertion flagged for resolution.
- `UNGROUNDED_SPECULATION`: Rejected or quarantined.

### Confidence Calibration
Claims are scored on a numerical range `[0.0, 1.0]` and grouped into rigorous tiers:
- `PROVEN` (`0.95 - 1.00`): Cryptographically or deterministically verified.
- `HIGH` (`0.80 - 0.94`): Authoritative primary sources or multi-model consensus.
- `MEDIUM` (`0.60 - 0.79`): Secondary evidence with plausible validity.
- `LOW` (`0.30 - 0.59`): Heuristic inference; requires user or empirical confirmation.
- `SPECULATIVE` (`0.00 - 0.29`): Unsubstantiated hypothesis; prohibited in production compilation.

---

## 3. Information Sufficiency & Adaptive Discovery

**Implementation Source**: `promptiq/discovery/sufficiency.py` (`InformationSufficiencyEvaluator`)

### Discovery Profiles
Supports 8 specialized discovery modes:
- `QUICK`: Minimal high-leverage intake for rapid prompt generation.
- `GUIDED`: Interactive step-by-step requirements gathering for typical workflows.
- `DEEP`: Exhaustive boundary, security, and edge-case elicitation.
- `TECHNICAL`: Focus on APIs, protocols, data schemas, and runtime constraints.
- `RESEARCH`: Evidence-seeking for academic, scientific, or market intelligence.
- `BUSINESS`: ROI, stakeholder, SLA, and operational constraint modeling.
- `CREATIVE`: Tone, stylistic nuance, and audience persona calibration.
- `AGENTIC`: Tool boundaries, state transitions, memory scopes, and permission envelopes.

### Decision-Value Question Ranking
Questions are dynamically prioritized by decision value:
$$\text{Priority} = \frac{\Delta \text{Uncertainty} \times \text{Impact}}{\text{Cognitive Overhead}}$$
This guarantees that questions with the greatest impact on prompt execution success are asked first, while frivolous questions are suppressed.

---

## 4. Constitution Change Impact Analysis

**Implementation Source**: `promptiq/services/impact_analyzer.py` (`ConstitutionChangeImpactAnalyzer`)

### Safety Mechanisms
1. **Requirement DAG Validation**:
   - Detects cyclic dependencies between requirements.
   - Detects dangling dependencies (references to non-existent requirement IDs).
2. **Impact & Drift Analysis**:
   - Analyzes additions, modifications, and deletions between constitution versions.
   - Flags breaking changes where modified or deleted requirements are depended upon by active downstream tasks.
   - Triggers downstream prompt recompilation recommendations when core invariants change.

---

## 5. Ten Task Families & Compiler Specialization

**Implementation Source**: `promptiq/registry/task_families.py` (`TaskFamilyRegistry`)

1. `prompt_synthesis`: Token density optimization, ambiguity elimination.
2. `software_engineering`: Clean architecture, test-driven contracts, zero-frontend enforcement.
3. `data_analysis`: Deterministic SQL/Pandas transformations, data lineage verification.
4. `creative_writing`: Narrative arc, voice consistency, stylistic constraints.
5. `business_strategy`: Risk assessment, KPI alignment, actionable roadmaps.
6. `academic_research`: Citation integrity, methodology transparency, epistemic bounds.
7. `ai_agent_development`: Tool execution safety, state management, permission isolation.
8. `api_design`: RESTful semantics, idempotency, strict JSON schema contracts.
9. `security_audit`: Threat modeling (STRIDE), vulnerability verification, secret redaction.
10. `workflow_automation`: Idempotent state machines, retry policies, durable execution.

Each task family defines:
- Planning rules and critical path defaults.
- Tailored discovery profiles and information sufficiency thresholds.
- Specialized PPS schema validation rules.
- Compiler-level guidance (e.g. XML tags, markdown contracts).
- Autopsy failure mode emphasis.
- Test Lab verification methodology and acceptance criteria.
