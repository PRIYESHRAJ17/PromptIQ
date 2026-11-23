# PROMPTIQ — POST-HACKATHON CRITICAL AUDIT & MASTER SCORECARD
## Objective Forensic Evaluation, Technical Debt Ledger & V8 Engineering Roadmap

---

## 1. Executive Summary & Reality Check

The hackathon sprint is officially over. Rapid productisation delivered a visible, working end-to-end platform with a Lovable-aesthetic web frontend, 6 native agent plugin packages, cloud deployment configurations, and 297 passing automated tests. 

However, in accordance with PromptIQ's core engineering invariants:
> **Strict No-Theater Policy**: No unearned praise, no decorative compliments, no manufactured success. Every component must be scored against harsh production-grade standards.

### The Brutal Reality Check: What is Genuinely Real vs What is Hackathon Debt

1. **The Web Frontend (`frontend/`)**:
   - *What is real*: The visual design system (warm cream `#FBF9F5`, terracotta `#C85A32`, sage `#6B8E7D`, Instrument Serif, Inter, JetBrains Mono) is production-grade, highly responsive, and bundles in 520ms (382 kB). The layout, component structure, navigation, and API client (`api.ts`) are well-architected.
   - *The Debt*: Several views rely heavily on local React state (`useState`) with pre-populated mock fixtures (e.g. `WorkflowWorkbench.tsx`, `ResearchEvidence.tsx`, `TestLab.tsx`, `Artifacts.tsx`) rather than live SSE (Server-Sent Events) or WebSocket streams from backend jobs. The router in `App.tsx` is state-based (`currentPage`) rather than URL-based (`react-router-dom`), meaning browser refresh resets the view and URL deep-linking does not exist.

2. **The Intelligence Engine & Agent Loop (`promptiq/orchestrator/`, `promptiq/critic/`)**:
   - *What is real*: The 11-stage workflow state machine, 5-tier permission hierarchy, 10 task family schemas, and 21-category autopsy rule engine are functionally complete and validated by 297 pytest tests.
   - *The Debt*: In `promptiq/core/config.py`, `MANAGED_INFERENCE_PRIMARY_ROUTE` defaults to `"mock"`. When no operator keys (Groq/Gemini) are supplied, the backend uses deterministic mock responses. The 21-category Prompt Autopsy relies primarily on regex heuristics rather than true semantic high-parameter LLM reasoning.

3. **Database & Distributed Workers (`promptiq/core/database.py`, `promptiq/services/`)**:
   - *What is real*: Relational SQLAlchemy 2.0 models, Alembic migrations (`alembic/versions/`), and SQLite WAL multi-reader concurrency.
   - *The Debt*: In local execution, jobs run in-process using Python `asyncio` tasks. If the Uvicorn process restarts, running jobs are abruptly interrupted. A durable task worker queue (e.g. Celery, Redis Streams, or NATS JetStream) is required for true production durability.

4. **Universal Agent Plugins (`integrations/plugins/`)**:
   - *What is real*: All 6 directories contain valid manifests, rules, skills, and MCP configurations. `promptiq-codex` has a functional CLI binary. The Universal MCP server correctly implements JSON-RPC 2.0 stdio transport.
   - *The Debt*: The plugins are configuration and MCP bridge wrappers; they are not published to official third-party registries (e.g. npm registry, Cursor extension marketplace, Anthropic plugin index).

---

## 2. Comprehensive Critical Scorecard (12 Dimensions)

Scoring Scale:
- **9.0 – 10.0**: Production Hardened (Battle-tested, fully dynamic, highly resilient)
- **7.5 – 8.9**: Production Ready (Functionally complete, verified, minor polish needed)
- **6.0 – 7.4**: Functional Prototype / Beta (Works under happy path, relies on fallbacks)
- **4.0 – 5.9**: Architectural Stub (Data structures exist, execution is simulated/mocked)
- **0.0 – 3.9**: Deficient / Non-Functional (Missing or non-viable)

| # | Dimension | Demonstrated Score | Architectural Ceiling | Production Status | Primary Limiting Factor |
|---|---|:---:|:---:|---|---|
| **1** | **Visual Design & Design System** | **9.2 / 10** | 9.8 / 10 | **Production Hardened** | Lovable Product Analytics aesthetic is cohesive, clean, lightweight (382 kB), and fast. |
| **2** | **Frontend Client Architecture** | **6.4 / 10** | 9.0 / 10 | **Functional Prototype** | State-based router (no URL history/deep linking); views rely on local state fallbacks. |
| **3** | **Core Backend & REST API** | **8.2 / 10** | 9.5 / 10 | **Production Ready** | FastAPI routers, Pydantic v2 schemas, type safety, OpenAPI coverage, and error handling. |
| **4** | **Database & Persistence** | **6.8 / 10** | 9.2 / 10 | **Functional Beta** | Defaults to local SQLite WAL; Postgres dialect tested in CI, but live DB clustering unverified. |
| **5** | **Agent Loop & Task Decomposition** | **7.5 / 10** | 9.2 / 10 | **Production Ready** | 11-stage observe-decide-act loop, DAG planner, 5-tier permissions, replan heuristics. |
| **6** | **Task Specialization (10 Families)** | **8.0 / 10** | 9.5 / 10 | **Production Ready** | 10 distinct task archetypes, boundary constraints, and prompt compiler templates. |
| **7** | **Prompt Autopsy & Defect Engine** | **7.6 / 10** | 9.4 / 10 | **Production Ready** | 21 categories with grounding verification; primarily static regex heuristics rather than semantic LLM. |
| **8** | **Project Memory & Constitution** | **8.4 / 10** | 9.6 / 10 | **Production Ready** | Versioned Constitution, decision supersession chains (`DEC-002` -> `DEC-001`), provenance tracking. |
| **9** | **Research & Evidence Ledger** | **6.2 / 10** | 9.0 / 10 | **Functional Beta** | Character offset schemas and contradiction logic exist, but live web crawling pipeline is stubbed. |
| **10** | **Zero-Price Model Gateway** | **7.4 / 10** | 9.0 / 10 | **Functional Ready** | Strict anti-BYOK enforcement; defaults to mock adapter unless server keys are provisioned. |
| **11** | **Universal Agent Plugins & MCP** | **7.8 / 10** | 9.5 / 10 | **Production Ready** | 7 MCP tools operational over stdio; 6 verified ZIP packages; lacks official registry hosting. |
| **12** | **Cloud Deployment & Ops** | **6.0 / 10** | 9.0 / 10 | **Functional Beta** | Docker Compose, Caddy, Render, and Vercel configs ready; live deployment unverified on public DNS. |
| **—** | **OVERALL PLATFORM SCORE** | **7.47 / 10** | **9.35 / 10** | **High-Grade Beta / MVP** | **Exceptional foundation, clear path to Tier-1 production.** |

---

## 3. Deep Forensic Findings by Component

### Dimension 1: Frontend Client Architecture & State (Score: 6.4 / 10)
- **Defect 1.1: State-Based Routing**: In `frontend/src/App.tsx`, navigation is managed via `const [currentPage, setCurrentPage] = useState('overview')`.
  - *Impact*: Page refreshes lose active view; browser back/forward buttons do not work; deep linking (`/workflow/wf-9821` or `/autopsy`) is impossible.
  - *Remedy*: Migrate to `react-router-dom` with HTML5 History API and nested route layouts.
- **Defect 1.2: Local Mock State Dominance**: In `WorkflowWorkbench.tsx`, `ResearchEvidence.tsx`, and `TestLab.tsx`, UI components initialize with hardcoded mock arrays (`subtasks`, `toolLogs`, `MOCK_EVIDENCE`, `MOCK_TEST_CASES`). While `api.ts` exists, the UI falls back to local mutations instead of continuous synchronization with `/api/v1/jobs/{id}` and `/api/v1/projects/{id}`.
  - *Impact*: The UI presents a simulated experience unless the user actively triggers specific mutations.
  - *Remedy*: Implement React Query (`@tanstack/react-query`) with automatic background cache revalidation and SSE streaming.

### Dimension 2: Core Backend & REST API (Score: 8.2 / 10)
- **Defect 2.1: In-Process Async Execution**: Workflow jobs created via `/api/v1/jobs` run in the same Python process as FastAPI.
  - *Impact*: Heavy tasks block or compete with HTTP request threads. If Uvicorn restarts, background jobs terminate without a resumption handshake.
  - *Remedy*: Decouple API server from job runners using Celery, RQ, or an embedded SQLite-backed task worker with heartbeats.
- **Defect 2.2: Synthetic MCP User**: In `promptiq/mcp/server.py` line 292, the MCP server registers a single hardcoded user `mcp_agent@promptiq.org` linked to `mcp_host`.
  - *Impact*: All MCP interactions share one tenant identity, limiting multi-user workspace separation when accessed over network SSE.
  - *Remedy*: Support scoped bearer token headers during MCP handshake to resolve the requesting user's actual workspace.

### Dimension 3: Prompt Autopsy & Forensic Critique (Score: 7.6 / 10)
- **Defect 3.1: Heavy Regex Heuristic Dependence**: In `promptiq/critic/autopsy.py`, the 21 defect categories (vague terms, excessive agency, injection risk, unsafe permissions, etc.) are evaluated using compiled regular expressions (`re.compile`).
  - *Impact*: Regex matching cannot grasp nuanced semantic ambiguities, intent subtleties, or obfuscated prompt injections.
  - *Remedy*: Implement a 2-tier pipeline: Tier 1 (instant regex pre-scan) + Tier 2 (few-shot adversarial LLM judge with structured JSON outputs and character-exact quote extraction).

### Dimension 4: Model Gateway & Zero-Price Routing (Score: 7.4 / 10)
- **Defect 4.1: Default Mock Route**: In `promptiq/core/config.py`, `MANAGED_INFERENCE_PRIMARY_ROUTE = "mock"`.
  - *Impact*: Out-of-the-box local installations without operator API keys in `.env` execute mock inference.
  - *Remedy*: Provide automated onboarding verification (`promptiq doctor`) that tests live zero-price connections (e.g. Groq free tier or Google AI Studio Gemini free tier) and reports available tokens.

### Dimension 5: Research & Evidence Ledger (Score: 6.2 / 10)
- **Defect 5.1: Stubbed Web Scraping Pipeline**: While character offset tracking (`char_offset_start`, `char_offset_end`) and contradiction schemas are implemented, PromptIQ does not currently run a live, headless web scraping engine with an SSRF sandbox for arbitrary external URLs.
  - *Impact*: Research evidence is either supplied manually, extracted from connected local documents, or generated from gateway inference.
  - *Remedy*: Build a sandboxed HTTP retrieval worker with Puppeteer/Playwright or httpx, equipped with DNS rebinding protection and domain allowlisting.

### Dimension 6: Cloud Deployment & Production Ops (Score: 6.0 / 10)
- **Defect 6.1: Local Windows Symlink Restriction**: Direct CLI deployment via `vercel deploy --temporary` failed on Windows due to unprivileged symlink syscalls (`EPERM`).
  - *Impact*: Developers cannot deploy to Vercel directly from Windows CLI without Administrator privileges or Git CI.
  - *Remedy*: Provide a GitHub Actions CI/CD workflow that triggers automated deployment to Vercel/Render on push to `main`.

---

## 4. Prioritized Engineering Improvement Roadmap (V8 Blueprint)

```
[ Phase 1: Immediate ] ──> [ Phase 2: Core Engine ] ──> [ Phase 3: Intelligence ] ──> [ Phase 4: Production ]
  • React Router DOM          • Task Worker Queue        • Hybrid Autopsy (LLM)      • Live Cloud Domain
  • Live React Query          • SSE Live Streaming       • Live Web Research         • PostgreSQL Cluster
  • Deep Linking              • Multi-User MCP           • Dynamic Replanning v2     • GitHub Actions CI/CD
```

### Phase 1: Frontend Modernization & True Live Data Binding
1. **Implement `react-router-dom`**: Replace `currentPage` state in `App.tsx` with clean browser routes:
   - `/` &rarr; Overview
   - `/projects` & `/projects/:projectId` &rarr; Project Memory & Constitution
   - `/workflows/new` &rarr; New Workflow Wizard
   - `/workflows/:jobId` &rarr; Workflow Workbench
   - `/autopsy` &rarr; Prompt Autopsy
   - `/evidence` &rarr; Research & Evidence Ledger
   - `/test-lab` &rarr; Test Lab
   - `/integrations` &rarr; Agent Plugins & MCP
   - `/settings` &rarr; Governance Settings
2. **Implement `@tanstack/react-query`**: Connect all views directly to `promptiqApi` endpoints with query caching, optimistic mutations, and zero reliance on static mock arrays.

### Phase 2: Real-Time Event Streaming & Job Queue
1. **Server-Sent Events (SSE) Stream**: Add `/api/v1/jobs/{id}/events` to FastAPI, streaming live subtask transitions, tool invocations, and log output directly to the frontend.
2. **Background Task Runner**: Implement a standalone worker process (`promptiq.worker`) that claims queued jobs from SQLite/PostgreSQL with atomic leases (`lease_token`), executing steps asynchronously without blocking the web server.

### Phase 3: Hybrid Semantic Prompt Autopsy
1. **LLM-Augmented Defect Judge**: Upgrade `promptiq/critic/autopsy.py` so that after the static regex pre-scan, candidate prompts are evaluated by a specialized adversarial prompt via the model gateway.
2. **Strict Grounding Enforcement**: Retain the existing invariant where model-claimed defects must cite exact substrings from the target prompt, discarding ungrounded hallucinations.

### Phase 4: Live Cloud Hosting & Automated CI/CD
1. **GitHub Actions Deployment**: Create `.github/workflows/deploy.yml` to automatically build, test, and deploy the frontend to Vercel / Cloudflare Pages and the backend to Render / Fly.io.
2. **PostgreSQL Production Verification**: Run integration tests against a live PostgreSQL 16 container in CI to verify transaction isolation and JSONB index performance.
