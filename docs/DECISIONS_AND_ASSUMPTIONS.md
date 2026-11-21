# PromptIQ Architectural Decisions and Assumptions Record

This document records the architectural choices, trade-off evaluations, locked product decisions, strategic hypotheses, and operational assumptions governing PromptIQ.

---

## 1. Locked Product Decisions (Non-Negotiable)

| Decision ID | Title | Principle | Rationale |
| :--- | :--- | :--- | :--- |
| **LDEC-001** | **Strictly No Website Frontend** | Section 0 | User explicitly prohibited website UI development until future UI templates are provided. The backend must provide complete APIs and contracts. |
| **LDEC-002** | **Zero-Price to End Users** | Section 4, Ch 20 | User-facing cost is ₹0. No subscriptions, credits, billing, or paywalls. Accessible to all users regardless of budget. |
| **LDEC-003** | **Strictly No BYOK / No User Keys** | Section 4, Ch 20.5 | Users are never asked to enter API keys for OpenAI, Anthropic, Gemini, Groq, or search engines. Eliminates credential leakage risks and UX friction. |
| **LDEC-004** | **No Local Model Installation** | Section 4, Ch 1 | Centrally hosted architecture. Does not require users to install Ollama, llama.cpp, or possess high-end GPUs. |
| **LDEC-005** | **Shared Central Model Route** | Section 4, Ch 14.5 | One centrally managed internal model experience powers the Web API, Telegram Bot, MCP server, and integrations. No internal model picker for users. |
| **LDEC-006** | **Three Connected Surfaces** | Section 5, Ch 2 | Web, Telegram, and Integrations share identical project identity, Project Constitution, discovery state, and context continuity. |

---

## 2. Technical Architecture Decisions & Trade-Offs

### ADR-001: Modular Monolith vs. Microservices
- **Decision**: Build PromptIQ as a **Modular Monolith**.
- **Alternatives Considered**: Microservice fleet (Auth service, Discovery service, Compilation service, Telegram service, Research service).
- **Trade-Off Analysis**:
  - *Microservices*: Massive operational overhead, distributed transaction complexity, network latency, difficult local testing, high infrastructure cost.
  - *Modular Monolith*: Strong internal domain boundaries, in-process function calls, shared database transactions, simple zero-cost local testing, single deployment artifact. Can be decomposed into microservices later if scale demands.
- **Outcome**: Adopt modular monolith organized by clean domain packages (`promptiq.core`, `promptiq.discovery`, `promptiq.compiler`, `promptiq.gateway`, etc.).

### ADR-002: Backend Language & Framework Selection
- **Decision**: **Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy 2.0**.
- **Alternatives Considered**:
  - *TypeScript/Node.js*: Strong web ecosystem, but inferior native tooling for complex AI research pipelines, prompt evaluations, data extraction, and machine learning utilities.
  - *Go*: Fast execution and concurrency, but rigid type system for complex heterogeneous AI intermediate representations and dynamic schema validation.
- **Trade-Off Analysis**:
  - Python is the undisputed standard in AI engineering, evaluation frameworks (Promptfoo, Langfuse, Ragas), and data processing. FastAPI provides high-performance async ASGI routing, automatic OpenAPI specification generation, and strict Pydantic v2 validation.
- **Outcome**: Implement backend in Python with strict typing and Pydantic models.

### ADR-003: Database Abstraction (SQLite for Test/Dev, PostgreSQL for Production)
- **Decision**: Use **SQLAlchemy 2.0 async engine** supporting both **SQLite (aiosqlite)** for deterministic, zero-dependency testing/local runs and **PostgreSQL (asyncpg)** for production deployments.
- **Trade-Off Analysis**:
  - Requiring a live PostgreSQL daemon for unit tests breaks out-of-the-box local execution and test velocity.
  - By writing dialect-neutral SQLAlchemy queries and storing complex nested structures in standardized JSON columns, tests run instantly in-memory or on local SQLite, while production seamlessly targets PostgreSQL.
- **Outcome**: Dual-dialect support configured via `DATABASE_URL`.

### ADR-004: Centrally Managed Zero-Price Inference Strategy
- **Decision**: Implement a **Zero-Price Inference Gateway** utilizing operator-managed free tier allocations (Gemini Developer API, Groq Free Tier, OpenRouter $0 models) backed by a hard **Zero-Price Enforcement Gate** and an in-memory **Deterministic Mock Adapter**.
- **Trade-Off Analysis**:
  - Provider free tiers have strict rate limits and data use terms.
  - Hard gate guarantees no billable routes are ever invoked. If capacity is exhausted, the system queues requests or pauses gracefully with honest user status rather than attempting paid fallback.
  - Automated CI tests use the deterministic mock adapter to ensure zero external network calls, zero rate-limiting, and 100% test reliability.
- **Outcome**: Dedicated `promptiq.gateway` module with strict capacity and eligibility controls.

---

## 3. Assumptions & Hypotheses

| Assumption ID | Description | Validation Method | Risk / Contingency |
| :--- | :--- | :--- | :--- |
| **ASSUMP-001** | Provider free tier quotas (e.g. Gemini, Groq) provide sufficient throughput for initial MVP testing and usage. | Continuous capacity tracking via Capacity Governor. | If quotas tighten, queue requests and throttle concurrent jobs. |
| **ASSUMP-002** | Target agent environments (Antigravity, Claude Code, Cursor, Codex) maintain their documented plugin/rule loading conventions. | Adapter compatibility test suite against official specifications. | Versioned adapters with explicit compatibility flags (`SUPPORTED`, `STALE`, `UNVERIFIED`). |
| **ASSUMP-003** | Telegram Bot API webhook or long-polling provides responsive conversational discovery on mobile. | Integration tests using mock Telegram updates and message assertions. | Respect 4096-character message limits by chunking or linking to export dossiers. |
