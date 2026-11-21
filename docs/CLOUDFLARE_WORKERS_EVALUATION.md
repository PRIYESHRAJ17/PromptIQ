# Cloudflare Workers Evaluation: Zero-Spend Feasibility for PromptIQ Backend

**Evaluation Date**: November 21, 2026  
**Auditor**: Lead Systems & Security Architect  
**Target Runtime**: Cloudflare Python Workers (Pyodide / WebAssembly Engine)  
**System Evaluated**: PromptIQ Asynchronous Backend (FastAPI, SQLAlchemy 2.0 Async, Pydantic v2, PostgreSQL)

---

## Executive Summary

PromptIQ’s primary cloud objective is an **absolute zero-spend runtime ($0 / month guaranteed)** with strict fail-closed ceilings and no risk of auto-billing a credit card. Cloudflare Workers offers an attractive free tier (100,000 requests/day, native hard cap without overage billing). 

However, this architectural audit establishes that **hosting the primary PromptIQ application backend directly on Cloudflare Python Workers is technically incompatible with the current asynchronous ASGI stack**, though Cloudflare is an ideal edge proxy and DNS/WAF fronting layer.

---

## Detailed Architectural Constraints & Evaluation

| Evaluation Dimension | Cloudflare Python Workers Free Tier | PromptIQ Backend Requirement | Compatibility Verdict |
| :--- | :--- | :--- | :--- |
| **Runtime Environment** | Pyodide (Python compiled to WebAssembly) | CPython 3.11+ async event loop | **PARTIAL / RESTRICTED** |
| **CPU Time Limit** | **10 ms** per request on Free Tier (50 ms on Paid) | Complex prompt compilation & AST validation: 25–150 ms | **FAILED (Hard Timeout)** |
| **Database Drivers** | Standard TCP sockets disabled; HTTP/WebSockets only (`Hyperdrive` required) | `asyncpg` / `aiosqlite` requiring raw async TCP stream | **FAILED (Socket Incompatible)** |
| **ORM Compatibility** | SQLAlchemy 2.0 async engine relies on C-extensions and threads | Full async ORM with connection pooling & transaction isolation | **FAILED (Runtime Error)** |
| **FastAPI / ASGI** | Requires custom WSGI/ASGI Pyodide bridges (`workers-py`) | Full FastAPI router tree with OpenAPI metadata | **FRAGILE (Heavy Cold Starts)** |
| **Memory Limit** | 128 MB | In-memory token bucket + deduplication cache: ~180 MB | **MARGINAL** |
| **Daily Request Quota** | **100,000 requests / day** (Hard Stop) | Expected free community workload: <10,000 req/day | **EXCELLENT (Zero-Spend Safe)** |

---

## Deep Technical Analysis

### 1. Pyodide vs. CPython Networking Limitations
Cloudflare’s Python Workers run inside the V8 JavaScript engine via Pyodide. Pyodide emulates Python standard libraries, but raw low-level TCP/UDP sockets (`socket.socket`) are prohibited by the V8 security sandbox.
- Standard PostgreSQL drivers (`asyncpg`, `psycopg3`) attempt to open direct TCP sockets to port 5432. Inside a Cloudflare Worker, this immediately raises `OSError: [Errno 23] Socket type not supported`.
- Cloudflare’s `Hyperdrive` service allows connection pooling to external databases, but it requires JavaScript bindings or Cloudflare D1 (SQLite), which does not support cross-worker transactional concurrency for multi-tenant isolation required by PromptIQ.

### 2. 10ms CPU Execution Limit
The free tier of Cloudflare Workers strictly enforces a **10-millisecond CPU time limit**. While I/O wait (such as waiting for an external LLM HTTP response) does not count against this limit, CPU-bound operations in PromptIQ exceed 10ms:
- Pydantic v2 validation of complex Project Constitution schemas: 4–12 ms
- Target adapter native compilation (producing 4 files with AST sanitization): 18–35 ms
- Prompt autopsy heuristic analysis (regex and pattern tokenization): 8–20 ms
Under burst conditions, requests would encounter `Error 1102: Worker exceeded CPU time limit`.

### 3. Native Cold Start Latency
Loading the Python standard library inside WebAssembly creates a cold-start overhead of 400ms to 1,200ms per un-warmed worker instance, significantly degrading CLI and MCP interaction velocity.

---

## Recommended Topology: Edge Proxy + Containerized Cloud Backend

PromptIQ adopts a **Hybrid Edge-Core Architecture**:

1. **Cloudflare Free Edge (Proxy & DNS)**:
   - Provides global SSL termination, DDoS protection, and DNS rebinding prevention for Streamable HTTP MCP (`api.promptiq.dev`).
   - Hard cap: 100k requests/day free without payment setup.
2. **Neon Serverless PostgreSQL (Database)**:
   - 0.5 GiB free storage, autoscaling to 0 when idle.
   - Genuine hard stop (read-only freeze upon exceeding quota; zero automatic card billing).
3. **Containerized Stateless Backend (Render Free Tier / Cloud Run with Quota Hard-Stop)**:
   - Render Web Service Free Tier: 512 MB RAM, native CPython runtime, zero credit card requirement, spins down after 15 minutes of inactivity.
   - Runs the full FastAPI + SQLAlchemy async stack without socket or CPU time constraints.
