# PromptIQ Product Roadmap & Release Gates

## 1. Release Progression & Quality Gates

The product roadmap follows the staged releases established in Chapter 24 of the Master Product Blueprint.

```
R0: Foundations ──► R1: Core & APIs ──► R2: Bot & Integrations ──► R3: Research ──► R4: Continuity ──► R5: Test Lab ──► R6: Hardening
```

---

### Release 0 (R0): Architectural Validation & Foundation
- **Milestone Scope**: Traceability matrix, system architecture, database models, zero-price gateway, and testing harness.
- **Exit Gate**: All core policies locked; deterministic test suite passing; git repository configured.

### Release 1 (R1): Prompt Intelligence Core & API
- **Milestone Scope**: Adaptive Discovery (4-input intake, Quick/Guided/Deep, Software stages A-K), Project Constitution with provenance and immutable versioning, PPS schema, and initial Prompt-only / Prompt-suite generation.
- **Exit Gate**: User can define project requirements, generate structured prompt suites, and inspect requirement traceability.

### Release 2 (R2): Telegram Bot & Target Adapters
- **Milestone Scope**: Telegram Bot companion, cross-surface state synchronization, and native adapters for Google Antigravity, Claude Code, OpenAI Codex, Cursor, and Gemini CLI.
- **Exit Gate**: Same project accessible and editable from Web API and Telegram Bot; native packages validate against target schemas.

### Release 3 (R3): Research Intelligence & Registries
- **Milestone Scope**: Research Intelligence Engine, query decomposition, Evidence Ledger, Model Registry, and Environment Registry.
- **Exit Gate**: Factual claims link to primary sources, dates, and locators; stale/unknown target statuses are visibly marked.

### Release 4 (R4): Project Memory & Continuity
- **Milestone Scope**: Context Compiler, token budget packing, milestone checkpoints, cross-agent handoff packaging, and conflict resolution.
- **Exit Gate**: Handoff preserves 100% of confirmed requirements; checkpoint recovery eliminates duplicate context entry.

### Release 5 (R5): Prompt Test Lab & Failure Intelligence
- **Milestone Scope**: Test suite generation, deterministic assertions, Promptfoo configuration export, comparative benchmarking, and failure intelligence store.
- **Exit Gate**: Controlled baseline vs. improved prompt comparison with reproducible metric reports.

### Release 6 (R6): Production Hardening & Ecosystem
- **Milestone Scope**: Model Context Protocol (MCP) server, Python CLI & SDK, security audit, secret redaction, OpenTelemetry observability, and comprehensive OpenAPI documentation.
- **Exit Gate**: Zero critical/high static analysis or security findings; 100% automated test pass rate.
