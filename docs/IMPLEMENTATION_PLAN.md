# PromptIQ Engineering Implementation Plan

This implementation plan outlines the staged roadmap for delivering the complete PromptIQ product foundation across Milestones 0 through 11.

---

## Milestone Schedule & Deliverables

### Milestone 0: Foundations & Invariants Setup
- **Goal**: Establish project core, requirements traceability, architecture specifications, git repository, persistent rules, and linting/testing toolchain.
- **Deliverables**:
  - `AGENTS.md` and `GEMINI.md` defining project non-negotiables.
  - Complete `/docs/` suite (Traceability, Architecture, Security, Decisions, Integration, Test Strategy, Roadmap, Changelog).
  - Virtual environment configuration and pinned dependencies.
  - Automated linting (`ruff`), typing, and testing harness (`pytest`).
- **Exit Gate**: Clean static checks, git initialized, all governance documents committed.

### Milestone 1: Identity, Workspaces & Project Foundations
- **Goal**: Implement multi-tenant identity, workspace security boundaries, relational database schemas, and project management.
- **Deliverables**:
  - SQLAlchemy models: `User`, `Workspace`, `WorkspaceMembership`, `Project`, `ProjectMembership`, `AuditEvent`.
  - Database engine abstraction supporting SQLite (development/tests) and PostgreSQL (production).
  - Authentication service: JWT issuance, password hashing, and API key management.
  - Project Service: CRUD operations, workspace tenancy checks, audit logging.
- **Exit Gate**: 100% passing tests for tenant isolation, authentication, and project lifecycle.

### Milestone 2: Adaptive Discovery & Project Constitution
- **Goal**: Build the conversational intake and versioned Project Constitution engine.
- **Deliverables**:
  - Initial 4-input intake handler (`Goal`, `Deliverable`, `Target`, `Context`).
  - Adaptive discovery engine with `Quick`, `Guided`, and `Deep` pipelines.
  - 11-stage software project discovery (Stages A through K).
  - Context extractor for uploaded files and pasted text.
  - `ProjectConstitution` with immutable versions, provenance metadata (`user_provided`, `inferred`, etc.), and approval/diff engine.
- **Exit Gate**: Full discovery workflow tests, provenance verification, immutable constitution snapshots.

### Milestone 3: Prompt Intelligence & Target Compilation
- **Goal**: Implement the PromptIQ Prompt Specification (PPS) intermediate representation and native target compilers.
- **Deliverables**:
  - Pydantic PPS schema and validation engine.
  - Model Registry & Environment Registry.
  - Target Compilers:
    - Google Antigravity native plugin adapter (`plugin.json`, `skills/`, `rules/`, `agents/`, `hooks/`).
    - Claude Code adapter (`CLAUDE.md`, rules, settings).
    - OpenAI Codex / ChatGPT plugin adapter.
    - Cursor adapter (`.cursorrules`, MCP config).
    - Gemini CLI adapter.
    - Prompt-only and Prompt-suite raw formatters.
- **Exit Gate**: Target compiler tests validating generated manifests against environment schemas.

### Milestone 4: Prompt Autopsy & Research Intelligence
- **Goal**: Deliver adversarial critical review and evidence-based research engine.
- **Deliverables**:
  - Prompt Autopsy analyzer evaluating ambiguity, missing requirements, contradictions, security, and context fit.
  - Structured `CriticFinding` generation with severity, impact, and fixes.
  - Research Intelligence Engine with query decomposition, source hierarchy, and SearXNG/mock connectors.
  - Evidence Ledger tracking claims, sources, retrieval dates, locators, and contradiction status.
- **Exit Gate**: Critique tests detecting prompt flaws; research tests verifying evidence ledger integrity.

### Milestone 5: Centrally Managed Zero-Price Inference Gateway
- **Goal**: Implement zero-price routing, capacity governance, and test mocks.
- **Deliverables**:
  - Inference Gateway with strict zero-price eligibility gate (rejects paid routes, enforces $0).
  - Capacity Governor: fair-use token bucket, concurrency limiter, request de-duplication, circuit breaker.
  - Provider adapters: Google Gemini Developer API (free tier), Groq (free tier), OpenRouter ($0 variants).
  - Deterministic mock adapter for automated offline testing.
- **Exit Gate**: Hard gate tests verifying zero-price enforcement, absence of BYOK, and pause-on-exhaustion.

### Milestone 6: Project Memory & Context Continuity
- **Goal**: Build durable context compilation, checkpointing, and cross-session handoff.
- **Deliverables**:
  - Context Compiler: token estimation, relevance filtering, priority packing of Constitution items.
  - Checkpoint manager: state snapshots, blocker tracking, next action plans.
  - Cross-agent handoff packaging and version conflict resolution.
- **Exit Gate**: Context continuity tests verifying zero requirement loss during agent handoffs.

### Milestone 7: Prompt Test Lab & Benchmarking
- **Goal**: Deliver prompt execution benchmarking and Promptfoo integration.
- **Deliverables**:
  - Prompt Test Lab: test case generation, deterministic assertions, baseline vs improved comparison.
  - Promptfoo configuration generator and test runner.
  - Failure intelligence store tracking failure hypotheses and regression test seeds.
- **Exit Gate**: Benchmark comparison tests producing structured pass-rate and latency reports.

### Milestone 8: Telegram Bot Companion
- **Goal**: Build a fully functional Telegram bot client connecting to the shared backend.
- **Deliverables**:
  - Telegram Bot engine using official Bot API.
  - Commands: `/start`, `/generate`, `/review`, `/improve`, `/research`, `/build`, `/projects`, `/resume`, `/export`.
  - Conversational discovery interview flow with inline keyboard menus.
  - Account linking via secure signed tokens.
- **Exit Gate**: Telegram bot tests covering conversational flows, project creation, and notifications.

### Milestone 9: Model Context Protocol (MCP) Server, CLI & SDK
- **Goal**: Expose PromptIQ tools to external agents and developer workflows.
- **Deliverables**:
  - MCP JSON-RPC Server implementing `forge.*` tools (`create_project`, `run_discovery`, `compile_prompt`, etc.).
  - Python SDK client (`promptiq.sdk.PromptIQClient`).
  - Command Line Interface (`promptiq.cli`).
- **Exit Gate**: MCP protocol conformance tests, CLI execution tests.

### Milestone 10: Production Hardening, Security & Operations
- **Goal**: Security audits, static analysis, performance checks, and operational runbooks.
- **Deliverables**:
  - Security hardening: input sanitization, OWASP GenAI Top 10 defenses, token redaction.
  - OpenTelemetry observability, health check endpoints, and structured JSON logging.
  - Code quality reports and security finding remediations.
- **Exit Gate**: Zero critical/high static analysis or security findings; 100% test suite passing.

### Milestone 11: Final Delivery & Documentation
- **Goal**: Final verification, OpenAPI specification generation, developer documentation, and delivery report.
- **Deliverables**:
  - Comprehensive OpenAPI JSON/YAML export.
  - Production runbooks and operational documentation.
  - Final Milestone Delivery Report.
