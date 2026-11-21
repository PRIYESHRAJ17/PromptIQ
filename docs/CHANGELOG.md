# PromptIQ Engineering Changelog

All notable changes to the PromptIQ product foundation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-11-21

### Added
- **Milestone 0: Specification & Foundation**:
  - Full extraction and analysis of `PromptIQ_Master_Product_Blueprint_v1.2.docx`.
  - Initialized local Git repository with production `.gitignore`.
  - Authored root persistent Antigravity instructions: `AGENTS.md` and `GEMINI.md`.
  - Established complete documentation suite in `/docs/` (Traceability, Architecture, Implementation Plan, Security, Policies, Integration Matrix, Test Strategy, Quality Reports).
  - Configured Python 3.13 virtual environment with FastAPI, Pydantic v2, SQLAlchemy 2.0, aiosqlite, Alembic, httpx, pytest, pytest-asyncio, and ruff.

- **Milestone 1: Identity, Workspaces & Project Foundations**:
  - Built multi-tenant SQLAlchemy relational data models (`User`, `Workspace`, `WorkspaceMembership`, `Project`, `ProjectMembership`, `AuditEvent`).
  - Implemented password hashing (`passlib` PBKDF2-SHA256) and signed JWT authentication tokens.
  - Implemented `ProjectService` with strict row-level workspace tenant isolation.

- **Milestone 2: Adaptive Discovery & Project Constitution**:
  - Initial 4-input intake handler (`goal`, `deliverable`, `target`, `context`).
  - Adaptive Discovery Coordinator supporting `Quick`, `Guided`, and `Deep` pipelines with anti-fatigue checks.
  - Task-specific discovery paths for prompt creation, prompt improvement, research, agent creation, and prompt evaluation.
  - 11-stage software project discovery (Stages A through K).
  - Context extractor for pasted text and files with strict provenance labeling (`user_provided`, `file_extracted`, `inferred`).
  - `ProjectConstitution` with immutable versions (`ConstitutionVersion`), granular diffing, and user approval gates.

- **Milestone 3: Prompt Intelligence & Target Compilation**:
  - Strongly typed PromptIQ Prompt Specification (`PromptSpecSchema` / PPS).
  - Model Registry & Environment Registry with capability metadata and verified pricing.
  - Target-native compilation adapters:
    - Google Antigravity (`plugin.json`, `AGENTS.md`, `skills/`, `rules/`)
    - Claude Code (`CLAUDE.md`, `.claude/settings.json`)
    - Cursor (`.cursorrules`, `.cursor/rules/`, `.cursor/mcp.json`)
    - OpenAI Codex (`.well-known/ai-plugin.json`, `openapi.yaml`)
    - Gemini CLI (`gemini-extension.json`, `context/`)
    - Raw prompt and prompt suite formatters.

- **Milestone 4: Prompt Autopsy & Research Intelligence Engine**:
  - `PromptAutopsyEngine` evaluating ambiguity, excessive agency, injection risks, and missing error contracts.
  - Structured `CriticFindingSchema` generation with severity, consequence, and remediation.
  - `ResearchEngine` with query decomposition, source hierarchy, and SearXNG/mock connectors.
  - Immutable `EvidenceClaim` and `SourceRecord` persistence in the Evidence Ledger.

- **Milestone 5: Centrally Managed Zero-Price Inference Gateway**:
  - Hard zero-price eligibility gate (`verify_zero_price_route`) rejecting any non-zero price route.
  - Prohibited BYOK gate (`check_and_reject_byok`) rejecting user-supplied API keys.
  - `CapacityGovernor` with sliding-window user fair-use limits, concurrency caps, deduplication cache, and circuit breakers.
  - Provider adapters for Google Gemini Developer API (free tier), Groq (free tier), OpenRouter ($0 variants), and deterministic mock.

- **Milestone 6: Project Memory, Checkpointing & Context Continuity**:
  - `ContextCompiler` with token budget estimation, priority packing, and on-demand truncation.
  - `CheckpointManager` recording verified milestone states, blockers, and next actions.

- **Milestone 7: Prompt Test Lab & Benchmarking**:
  - `PromptTestLab` running deterministic assertions (`contains`, `not_contains`, `regex`).
  - Automated failure intelligence recording (`FailureRecord`).
  - `PromptfooExporter` translating test suites into Promptfoo-compatible YAML/JSON structures.

- **Milestone 8: Telegram Bot Companion**:
  - `TelegramBotClient` implementing `/start`, `/build`, `/generate`, `/review`, `/research`, `/projects`.
  - Signed HMAC token verification for secure account linking.
  - Interactive inline keyboard menus.

- **Milestone 9: Model Context Protocol (MCP) Server, CLI & SDK**:
  - MCP JSON-RPC stdio server exposing 8 `forge.*` tools conforming to the MCP specification.
  - Programmatic Python client `PromptIQClient`.
  - Terminal CLI `promptiq` with `init`, `mcp`, `status`, and `review` subcommands.

- **Milestone 10: Security, Quality & Operations**:
  - Automated secret redaction filter for logs and outputs.
  - Input sanitization against control characters and null bytes.
  - In-memory `MetricsCollector` tracking requests, latency, errors, and token usage.
  - Comprehensive automated test suite with **32 passing tests out of 32 (100% pass rate)**.
  - Zero static analysis or linting warnings (`ruff check` clean).
