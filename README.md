# PromptIQ

**Universal Prompt Intelligence, Project Engineering, and Cross-Agent Continuity Platform**

PromptIQ is a vendor-neutral, prompt-first intelligence platform that turns human intent into deeply specified, researched, critically reviewed, and target-native AI instructions.

Powered by a single, centrally managed zero-price inference service, PromptIQ coordinates across three surfaces:
1. **API / Backend** (for future web workspace; frontend strictly out of scope)
2. **Telegram Bot** (conversational companion, intake, approvals, notifications)
3. **Agent Integrations** (Model Context Protocol / MCP, CLI, SDK, and native adapters for Google Antigravity, Claude Code, OpenAI Codex, Cursor, and Gemini CLI)

---

## Key Invariants
- **₹0 User Cost**: No subscriptions, usage bills, credits, or paywalls.
- **No BYOK**: Users never provide model or search API keys.
- **No Local Inference**: No local model installation (no Ollama / llama.cpp / local GPU requirements).
- **One Shared Core**: All surfaces share identity, Project Constitution, discovery state, and project memory.
- **Strictly No Website Frontend**: Implemented as an API-first backend with complete OpenAPI contracts.

---

## Directory Structure
```
promptiq/
  ├── api/              # FastAPI routers, dependencies, and middleware
  ├── core/             # Configuration, logging, database session, exceptions
  ├── models/           # SQLAlchemy relational models
  ├── schemas/          # Pydantic v2 schemas and validation models
  ├── services/         # Domain services (Auth, Project, Constitution)
  ├── discovery/        # Adaptive discovery (Quick, Guided, Deep, Software Stages A-K)
  ├── compiler/         # PPS intermediate representation & target compiler
  ├── adapters/         # Target-native adapters (Antigravity, Claude, Codex, Cursor, Gemini)
  ├── registry/         # Model Registry & Environment Registry
  ├── critic/           # Prompt Autopsy & adversarial critique engine
  ├── research/         # Research Intelligence Engine & Evidence Ledger
  ├── orchestrator/     # Specialist task graph orchestrator
  ├── eval/             # Prompt Test Lab, assertions, Promptfoo exporter
  ├── memory/           # Durable project memory, context compiler, checkpoints
  ├── gateway/          # Zero-price inference gateway & capacity governor
  ├── telegram/         # Telegram Bot client & conversation handler
  ├── mcp/              # Model Context Protocol JSON-RPC server
  ├── cli/              # PromptIQ terminal CLI
  ├── sdk/              # Python client SDK
  └── observability/    # Metrics, audit trails, and health monitors
tests/                  # Comprehensive automated test suite
docs/                   # Specifications, architecture, and governance docs
```

---

## Quickstart

### Prerequisites
- Python >= 3.11

### Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Run Tests
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Run Static Analysis
```powershell
.\.venv\Scripts\python.exe -m ruff check promptiq/ tests/
```

### Start Backend API Server
```powershell
.\.venv\Scripts\python.exe -m uvicorn promptiq.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at: `http://localhost:8000/docs`.

### Start MCP Server
```powershell
.\.venv\Scripts\python.exe -m promptiq.mcp.server
```

### CLI Commands
```powershell
.\.venv\Scripts\python.exe -m promptiq.cli.main --help
```
