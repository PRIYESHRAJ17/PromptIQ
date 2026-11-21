# PromptIQ Model Benchmark Methodology & Rubric Specification

**Version**: 2.0.0  
**Test Suite Path**: `data/model_benchmarks_v2/benchmark_cases.json`  
**Harness**: `ModelTournamentRunner` (`promptiq.eval.tournament`)  

---

## 1. Overview & Separation of Concerns

PromptIQ rejects synthetic benchmark conflation. The benchmark suite enforces strict separation between:
1. **Category A: Deterministic Invariant & Syntax Benchmarks**: Tests executed locally and objectively that measure schema conformance, invariant violation rejection, contradiction catching, negative constraints, and injection blocking.
2. **Category B: Live Provider Evaluations**: Real-world measurements recording HTTP response codes, actual latency, header rate limit metadata, and real token usage. If credentials are missing, tests report `UNVERIFIED` without manufactured metrics.

---

## 2. The 20 Benchmark Categories

| Category Index | Category ID | Evaluation Focus & Rubric | Pass Condition |
| :---: | :--- | :--- | :--- |
| **01** | `requirement_extraction` | Extraction of requirements with strict provenance metadata (`user_provided`, `inferred`, `connected_source`). | All provenance tags correctly applied; zero fabricated tags. |
| **02** | `adaptive_discovery` | Adaptive discovery questioning without re-asking established facts. | 3 high-leverage questions; 0 re-asked facts. |
| **03** | `project_planning` | Topologically sorted milestone decomposition with explicit entry/exit criteria. | Sequential dependency mapping without circular references. |
| **04** | `constitution_generation` | Formulation of immutable invariants and approval workflow rules. | Invariants strictly included; approval requirement specified. |
| **05** | `technical_architecture` | Asynchronous service design with connection pooling, recycling, and circuit breaking. | PgBouncer/connection pool recovery patterns present. |
| **06** | `complex_reasoning` | Multi-tiered token bucket refill calculation under burst constraints. | Mathematically proven refill and burst limits. |
| **07** | `contradiction_detection` | Latent conflict identification across mutually exclusive requirements. | Conflict identified; trade-off reconciliation proposed. |
| **08** | `prompt_engineering` | Target-native instruction generation (Antigravity, Codex, Cursor, Claude). | Target-native directory structure and rules applied. |
| **09** | `prompt_improvement` | Eliminating ambiguity, defining contracts, and hardening user prompts. | Idempotency, status codes, and JSON schemas injected. |
| **10** | `critical_prompt_autopsy` | Adversarial autopsy with severity ratings (CRITICAL, HIGH, MEDIUM) and consequence analysis. | Insecure instructions flagged; `BLOCKED` verdict emitted. |
| **11** | `research_synthesis` | Evidence Ledger verification with primary source locators and dated citations. | Factual MCP Streamable HTTP specifications accurately cited. |
| **12** | `coding_and_debugging` | Detection and correction of asynchronous race conditions using `asyncio.Lock`. | Thread/task-safe lock pattern correctly implemented. |
| **13** | `structured_json` | Pure JSON generation conforming to schema without markdown fences or filler. | `json.loads()` passes without regex cleansing. |
| **14** | `tool_calling` | Exact function call payload formulation matching parameter signatures. | Correct tool name and typed arguments formulated. |
| **15** | `long_context_handling` | Needle-in-a-haystack retrieval of isolated constraints across dense documents. | Specific partitioning and retention rule extracted accurately. |
| **16** | `instruction_adherence` | Negative constraint adherence (e.g. word bans, formatting bans). | Zero banned words appear in output. |
| **17** | `security_and_injection` | Resistance to indirect prompt injections and system overrides. | Override command refused; legitimate text preserved. |
| **18** | `multi_stage_consistency`| Entity and constraint continuity across multi-turn interactions. | Identifiers and zero-price invariant preserved without drift. |
| **19** | `robustness_under_ambiguity` | Safe degradation when essential execution parameters are missing. | Execution paused; required missing parameters requested. |
| **20** | `output_verification` | Self-verification and acceptance criteria checking. | Failed criteria accurately identified and cataloged. |
