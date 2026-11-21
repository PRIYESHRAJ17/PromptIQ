# PromptIQ Engineering Changelog

All notable changes to the PromptIQ product foundation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-11-21

### Phase 3: Model Intelligence Tournament & Cloud-Native Production Architecture

### Added
- **Cloud-Native Production Architecture (Laptop Independence)**:
  - Implemented 24/7 cloud-native deployment configuration (Google Cloud Run + Neon Serverless Postgres + Cloud Secret Manager + CI/CD).
  - Multi-stage production `Dockerfile` with dedicated non-root user `promptiq` (UID 10001) and `/health` probe.
  - Knative declarative spec (`deployment/cloud/cloudrun.yaml`) with `minScale: 0` for ₹0 idle operation.
  - Render blueprint (`deployment/cloud/render.yaml`) pointing to external managed PostgreSQL.
  - Terraform IaC (`deployment/terraform/`) for GCP Cloud Run v2, Secret Manager secrets, and IAM invoker.
  - GitHub Actions CI/CD workflows (`.github/workflows/ci.yml`, `deployment/ci/deploy.yml`) for automated testing, linting, migration verification, and container deployment.
  - Local container staging cluster (`deployment/docker/docker-compose.yml`) with PostgreSQL 16 Alpine.
- **Model Intelligence Tournament & Synthetic Benchmark**:
  - Developed synthetic evaluation dataset covering all 14 benchmark categories (`data/synthetic_model_benchmarks/tournament_cases.json`).
  - Developed tournament evaluation harness (`promptiq/eval/tournament.py`) and scoring engine.
  - Conducted frontier candidate tournament and terms audit (`docs/MODEL_TOURNAMENT.md`).
  - Designated Google Gemini Developer API (`gemini-2.0-flash` / `gemini-3.8-flash`) as Primary Internal Model and GroqCloud (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`) as Secondary Burst Fallback.
  - Enforced fail-closed behavior on unknown providers and added `RETIRED_MODELS` blacklist.
- **Remote Model Context Protocol (MCP) Architecture**:
  - Implemented Streamable HTTP / Server-Sent Events (SSE) remote MCP transport (`promptiq/mcp/remote.py`) supporting `/api/v1/mcp/sse`, `/api/v1/mcp/messages`, and stateless `/api/v1/mcp/rpc`.
  - Implemented lightweight local stdio client bridge (`promptiq/mcp/client_bridge.py`) for external developer agents.
  - Added database readiness probe `/ready` in FastAPI app.
- **Platform Portability & Windows Smart App Control**:
  - Injected `DISABLE_SQLALCHEMY_CEXT=1` to enforce pure-Python SQLAlchemy fallbacks, preventing Windows Smart App Control blocking unsigned `.pyd` binaries.
  - Created automated setup scripts: `scripts/setup_dev.py` and `scripts/setup_dev.ps1`.
- **Cloud Documentation Suite**:
  - `docs/CLOUD_ARCHITECTURE.md`: Complete topology, laptop independence boundaries, subsystems, ingress, persistence.
  - `docs/DEPLOYMENT_GUIDE.md`: Step-by-step provisioning guide for Neon, Secret Manager, Cloud Run, migrations, Telegram webhook, and acceptance testing.
  - `docs/OPERATIONS_RUNBOOK.md`: SOPs for health probes, quota exhaustion fail-closed handling, secret rotation, and webhook repair.
  - `docs/CLOUD_COST_AND_CAPACITY.md`: Exhaustive $0/month budget breakdown, ceilings, and financial safety boundaries.
  - `docs/DISASTER_RECOVERY.md`: RTO < 15m, RPO < 1h, Neon-to-Supabase failover procedure, logical backups.

### Fixed
- **Bandit B310 Mitigation**: Added strict `http://` and `https://` URI scheme verification in `promptiq/mcp/client_bridge.py`.
- **Editable Package Layout**: Configured `[tool.setuptools.packages.find] include = ["promptiq*"]` in `pyproject.toml`.
- **Telegram Bot Session Filtering**: Fixed `DiscoverySession` query in `promptiq/telegram/bot.py` to use `is_completed.is_(False)`.
- **Coverage & Quality Verification**: Expanded automated tests to **52 passed tests (100% pass rate)** with **76% statement coverage**, 0 Ruff errors, 0 Bandit issues, and 0 pip-audit vulnerabilities.

---

## [0.2.0] - 2026-11-21

### Phase 2: Adversarial Implementation Audit & Hardening

### Added
- **Database Migrations Framework (Alembic)**:
  - Initialized async Alembic engine (`alembic.ini`, `alembic/env.py`).
  - Generated initial schema migration `0001_initial_schema.py` covering all 22 database tables.
  - Added bidirectional upgrade/downgrade migration test in `tests/test_database_migrations.py`.
- **Live Research Retrieval Connector**:
  - Implemented `LiveWebSearchConnector` in `promptiq/research/connectors/live_search.py` querying public documentation APIs with zero-cost and fallback to deterministic mock.
- **Telegram Update Deduplication & Conversational Discovery**:
  - Added sliding-window `update_id` deduplication cache in `TelegramBotClient` to prevent duplicate processing on network retries.
  - Added conversational discovery interview continuation in Telegram without requiring slash commands.
  - Constant-time secret comparison with `secrets.compare_digest` on the Telegram webhook.
- **MCP Protocol Handshake & Security**:
  - Added full MCP protocol JSON-RPC 2.0 handshake support (`initialize`, `notifications/initialized`, and `ping`).
  - Switched fallback user password generation to `secrets.token_urlsafe(32)`.
  - Added `test_mcp_protocol_handshake` in `tests/test_mcp_server.py`.
- **Exhaustive Cross-Tenant IDOR Test Suite**:
  - Implemented `test_exhaustive_cross_tenant_idor_enforcement` covering all project-scoped routes.

### Changed / Modernized
- **Modern OpenAI Codex / Agent Instructions Adapter**:
  - Deprecated and removed obsolete `.well-known/ai-plugin.json` (OpenAI Plugins sunset April 2024).
  - Modernized `CodexTargetAdapter` to output `CODEX.md`, `AGENTS.md`, `.codex/instructions.md`, and `.codex/mcp.json`.
- **Google Antigravity Customization System Alignment**:
  - Verified and enhanced `AntigravityTargetAdapter` to strictly comply with `plugin.json` schema, `rules/AGENTS.md`, `mcp_config.json`, and valid frontmatter in `skills/implementation/SKILL.md`.
- **Default Network Binding**:
  - Hardened default API host binding from `0.0.0.0` to loopback `127.0.0.1`.

### Fixed
- **CQ-006 Clarification**: Confirmed `EvaluationSuite.project_id == project_id` and `PromptPackage.project_id == project_id` were correctly implemented in code; clarified documentation summary text typo.
- **Real IDOR in Adaptive Discovery**: Fixed `start_session` and `submit_answers` in `promptiq/discovery/adaptive.py` to enforce tenant ownership verification via `ProjectService.get_project`.
- **Real IDOR in Prompt Autopsy**: Fixed `/critic/autopsy` in `promptiq/api/routes/critic.py` to verify package project ownership before executing critique.
- **Vulnerability Remediation**: Upgraded pip to 26.3 resolving PYSEC-2026-3721 (verified 0 vulnerabilities with `pip-audit`).
- **Static Security Remediation**: Eliminated all Bandit SAST issues across 5,856 LOC (0 High, 0 Medium, 0 Low).
- **Test Suite Expansion**: Test suite increased to **39 passing automated tests (100% pass rate)**.

---

## [0.1.0] - 2026-11-21

### Added
- **Milestone 0: Specification & Foundation**:
  - Full extraction and analysis of `PromptIQ_Master_Product_Blueprint_v1.2.docx`.
  - Initialized local Git repository with production `.gitignore`.
  - Authored root persistent Antigravity instructions: `AGENTS.md` and `GEMINI.md`.
  - Established complete documentation suite in `/docs/` (Traceability, Architecture, Implementation Plan, Security, Policies, Integration Matrix, Test Strategy, Quality Reports).
  - Configured Python 3.13 virtual environment with FastAPI, Pydantic v2, SQLAlchemy 2.0, aiosqlite, Alembic, httpx, pytest, pytest-asyncio, and ruff.
- **Milestones 1-10 Foundation Implementation**.
