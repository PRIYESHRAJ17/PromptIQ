# PromptIQ

**Universal Prompt Intelligence, AI Workflow Orchestration, and Continuous Project Memory Platform**

PromptIQ is a production-grade, prompt-first intelligence platform that turns human intent into deeply specified, researched, critically reviewed, and target-native AI execution packages.

Powered by a centrally managed zero-price inference architecture, PromptIQ unifies developer workflows across web, terminal, IDE, and autonomous agents.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-297%20Passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-80%25-green.svg)](tests/)
[![Pricing](https://img.shields.io/badge/User%20Cost-%E2%82%B90%20Zero--Price-orange.svg)](#key-invariants)
[![MCP](https://img.shields.io/badge/MCP-RFC%20Compliant-purple.svg)](integrations/plugins/promptiq-mcp/)

---

## Key Invariants

- **₹0 User Cost**: 100% free forever. No subscriptions, credits, usage fees, or paywalls.
- **Strictly No BYOK**: Users never supply OpenAI, Anthropic, or Gemini API keys. No paid inference routes and no paid fallbacks.
- **No Local Inference**: 100% centrally hosted intelligence service. Zero Ollama, llama.cpp, or local GPU dependencies required.
- **Canonical Project Memory**: The immutable, versioned **Project Constitution** is the single source of truth across all product surfaces with explicit requirement provenance and decision supersession chains (`DEC-002` superseding `DEC-001`).
- **Forensic Prompt Autopsy**: Strict 21-category defect detection engine with actionable findings, severity rankings, evidence passages, and release gates. No decorative agent theater.

---

## Platform Architecture

```
                                [ Developer / User ]
                                         │
             ┌───────────────────────────┴───────────────────────────┐
             ▼                                                       ▼
   [ Web Application ]                                     [ Universal Agent Plugins ]
  React 19 + TypeScript                                    • Google Antigravity
  Vite 8 + Tailwind v4                                     • Claude Code CLI
  Lovable Warm Aesthetic                                   • Cursor IDE (.cursorrules)
  (http://localhost:5173)                                  • OpenAI Codex
             │                                             • Google Gemini CLI
             │                                             • Universal MCP Server
             └───────────────────────────┬───────────────────────────┘
                                         ▼
                             [ PromptIQ ASGI Backend ]
                             FastAPI • Python 3.11/3.13
                             SQLite WAL / PostgreSQL 16
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
   [ Intelligence Engine ]      [ Project Memory ]          [ Zero-Price Gateway ]
   • 10 Task Families           • Project Constitution      • Centrally Managed
   • 11-Stage Workflow Loop     • Decision Supersession     • Rate Limiting
   • 21-Category Autopsy        • Evidence Ledger           • Quota Governance
   • Deterministic Test Lab     • Character Offsets         • Anti-BYOK Filter
```

---

## Product Surfaces

### 1. Web Application (`frontend/`)
Built with the **Lovable Product Analytics** design system (warm cream `#FBF9F5`, terracotta `#C85A32`, sage `#6B8E7D`, charcoal `#1E2229`, Instrument Serif, Inter, and JetBrains Mono):
- **Command Center & Overview**: Daily execution metrics, 4 core KPI cards, recent executions ledger with direct workbench inspection.
- **Project Memory & Constitution**: Living constitution inspection, P0–P3 requirements with provenance tags (`user_provided`, `inferred`), decision log with supersession chains, interactive "New Project" and "Add Decision" modals.
- **New Workflow Wizard**: Multi-family goal configurator supporting 10 task families, 6 target environments, exploration depth slider, and preset objectives.
- **Workflow Workbench**: 11-stage pipeline stepper (Intent -> Discovery -> DAG -> Autopsy -> Verify), dependency DAG subtask cards, live sandboxed tool logs, and step forward controls.
- **Prompt Autopsy**: Adversarial forensic scanner detecting defects across 21 failure modes with release block checks.
- **Research & Evidence Graph**: Claim ledger with exact character offset citations (`[1420:1680]`) and contradiction alerts.
- **Test Lab**: Deterministic assertion runner, JSON Schema AST parity validator, and multi-pass consistency scoring (T=0.2).
- **Artifacts Browser**: Direct client-side file downloads with SHA-256 cryptographic verification.
- **Universal Integrations UI**: Copyable install commands, feature matrices, test steps, and live MCP handshake tester.

### 2. Universal Agent Plugins & MCP (`integrations/plugins/`)
Native, packaged, and verified distributions for the leading AI coding agents:
- **Google Antigravity**: [`integrations/plugins/promptiq-antigravity/`](integrations/plugins/promptiq-antigravity/) (`manifest.json`, `SKILL.md`, `rules/promptiq.md`, `mcp.json`).
- **Claude Code CLI**: [`integrations/plugins/promptiq-claude-code/`](integrations/plugins/promptiq-claude-code/) (`.claude-plugin/plugin.json`, `/autopsy`, `/constitution`, `/compile` commands).
- **Cursor IDE**: [`integrations/plugins/promptiq-cursor/`](integrations/plugins/promptiq-cursor/) (`.cursorrules`, `mcp.json`).
- **OpenAI Codex**: [`integrations/plugins/promptiq-codex/`](integrations/plugins/promptiq-codex/) (`package.json`, `promptiq-codex` executable binary, `codex.json`).
- **Google Gemini CLI**: [`integrations/plugins/promptiq-gemini-cli/`](integrations/plugins/promptiq-gemini-cli/) (`gemini-extension.json`, `GEMINI.md`).
- **Universal MCP Server**: [`integrations/plugins/promptiq-mcp/`](integrations/plugins/promptiq-mcp/) (RFC-compliant Model Context Protocol server exposing all 7 tools).
- **Distributable ZIP Archives**: Standalone ZIP packages with registered SHA-256 hashes in `dist/plugins/` and `frontend/public/dist/plugins/`.

---

## Directory Layout

```
PromptIQ/
  ├── promptiq/                 # Core Python backend package
  │     ├── api/                # FastAPI routers, endpoints, and middleware
  │     ├── core/               # Configuration, security, database sessions
  │     ├── models/             # SQLAlchemy relational models
  │     ├── schemas/            # Pydantic v2 validation contracts
  │     ├── services/           # Business logic (Auth, Project, Constitution, Jobs)
  │     ├── discovery/          # Adaptive intake & discovery engine
  │     ├── compiler/           # Prompt Specification (PPS) native compiler
  │     ├── critic/             # 21-category Prompt Autopsy & forensic engine
  │     ├── research/           # Fact verification & character-offset Evidence Ledger
  │     ├── eval/               # Test Lab, assertions, rubric evaluators
  │     ├── gateway/            # Zero-price inference gateway & governor
  │     └── mcp/                # RFC-compliant Model Context Protocol JSON-RPC server
  ├── frontend/                 # Production Web Application (React 19 + TypeScript + Vite 8)
  │     ├── src/pages/          # 10 integrated page views
  │     ├── src/components/     # Layout (Shell), Badges, StatCards
  │     ├── src/lib/            # Type-safe API client, constants, utils
  │     └── src/types/          # TypeScript interfaces mapping 1:1 to Pydantic models
  ├── integrations/plugins/     # 6 Native Agent Plugin packages
  │     ├── promptiq-antigravity/
  │     ├── promptiq-claude-code/
  │     ├── promptiq-cursor/
  │     ├── promptiq-codex/
  │     ├── promptiq-gemini-cli/
  │     └── promptiq-mcp/
  ├── dist/plugins/             # Validated ZIP distributions & packages_manifest.json
  ├── deployment/               # Production cloud configs (Docker, Compose, Render, Fly, Vercel, Caddy)
  ├── docs/                     # Comprehensive architecture, runbooks, and audit reports
  ├── tests/                    # 297 automated pytest unit, integration, and security tests
  └── promptiq-mcp.cmd          # One-click MCP server launcher for Windows
```

---

## Quickstart Guide

### 1. Clone & Set Up Python Virtual Environment
```powershell
git clone https://github.com/PRIYESHRAJ17/PromptIQ.git
cd PromptIQ
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### 2. Start the Backend API Server
```powershell
.\.venv\Scripts\python.exe -m uvicorn promptiq.api.main:app --host 127.0.0.1 --port 8000
```
- API Health Check: `http://localhost:8000/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### 3. Start the Frontend Web Application
In a new terminal window:
```powershell
cd PromptIQ
npm --prefix frontend install
npm --prefix frontend run dev
```
Open your browser to: **`http://localhost:5173/`**

### 4. Run the Universal MCP Server
From the repository root:
```powershell
.\promptiq-mcp.cmd
```
*(Or `.\.venv\Scripts\python.exe -m promptiq.mcp.server`)*

Test with a JSON-RPC ping:
```powershell
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | .\promptiq-mcp.cmd
```

### 5. Install & Test the Codex Plugin CLI
```powershell
npm install -g ./integrations/plugins/promptiq-codex
promptiq-codex
```

---

## Automated Test Suite & Verification

PromptIQ enforces rigorous automated testing across security, contract schema, distributed coordination, and zero-price validation:

```powershell
# Run full pytest suite (297 tests)
.\.venv\Scripts\python.exe -m pytest

# Run static analysis & style checks
.\.venv\Scripts\python.exe -m ruff check promptiq tests

# Run security & vulnerability scanning
.\.venv\Scripts\python.exe -m bandit -r promptiq -ll -q

# Verify frontend production build
npm --prefix frontend run build

# Package & verify all 6 agent plugins
python scripts/package_plugins.py
```

---

## Cloud Deployment

Production deployment configurations are prepared in `deployment/`:

- **Self-Hosted Docker Compose**:
  ```bash
  cd deployment
  docker compose -f docker-compose.prod.yml up -d --build
  ```
  Launches PostgreSQL 16, PromptIQ Backend, and Caddy reverse proxy with automatic TLS.

- **Render Cardless Cloud**:
  Connect repository to Render and select `deployment/render.yaml` Blueprint.

- **Vercel Static Hosting**:
  Deploy `frontend/` with routing and `/api/v1` proxying via `frontend/vercel.json`.

---

## Repository & License

- **GitHub Repository**: [https://github.com/PRIYESHRAJ17/PromptIQ](https://github.com/PRIYESHRAJ17/PromptIQ)
- **License**: Apache 2.0
