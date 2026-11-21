# PromptIQ Cloudflare Workers Runtime Compatibility Report

**Phase**: 3.4 Technical Feasibility Deep-Dive  
**Date**: November 21, 2026  
**Auditor**: Cloud Architecture & Systems Performance Group  
**Objective**: Evaluate whether the complete PromptIQ Python backend can run directly inside Cloudflare Python Workers on the free tier.

---

## 1. Technical Evaluation Summary

| Dimension | Cloudflare Python Workers Free Tier Limit | PromptIQ Workload Requirement | Compatibility Verdict |
| :--- | :--- | :--- | :---: |
| **Execution Sandbox** | V8 WebAssembly (Pyodide) | Standard CPython 3.11+ | **`INCOMPATIBLE`** (Heavy C-extensions fail) |
| **CPU Time per Request** | **10 milliseconds** (Free plan hard limit) | 50–250 ms (Pydantic parsing, AST compilation, JWT verification) | **`FAILED`** (Worker terminates with Error 1027) |
| **Network Sockets** | Web standard `fetch()` only; no raw TCP | Direct TCP socket required for `asyncpg` / PostgreSQL | **`FAILED`** (Cannot connect to Neon DB without Hyperdrive) |
| **Bundle Size** | 25 MB compressed script limit | Python virtualenv with dependencies > 80 MB | **`FAILED`** (Exceeds free script package size) |
| **Concurrency / Tasks** | Ephemeral request/response; no background daemons | Async background task graph runner & research engine | **`INCOMPATIBLE`** (Long-running tasks terminated) |
| **Edge Ingress / WAF** | 100,000 requests/day, native TLS, DDoS protection | HTTPS ingress, IP rate limiting, webhook verification | **`FULLY COMPATIBLE`** (Ideal role) |

---

## 2. In-Depth Technical Incompatibilities

### 2.1 The 10 ms CPU Execution Time Limit
On Cloudflare Workers Free Tier, requests are restricted to **10 ms of actual CPU time** (excluding wall-clock network wait time).
- PromptIQ executes cryptographic hashing (`bcrypt` / HMAC-SHA256 for Telegram tokens), complex Pydantic v2 schema serialization, AST parsing of prompt templates, and multi-model consensus adjudication.
- Benchmarks on standard Python AST parsing and Pydantic validation demonstrate average CPU times of **35 ms to 90 ms**, causing immediate worker termination on Cloudflare's free plan (`Worker exceeded CPU time limit`).

### 2.2 Lack of Raw TCP Sockets for `asyncpg` and PostgreSQL
- PromptIQ's persistence layer is built on `asyncpg` and SQLAlchemy 2.0. Standard PostgreSQL protocols require raw TCP socket connections.
- Cloudflare Workers Python environment (Pyodide) intercepts network I/O through the JavaScript `fetch()` API. It cannot open raw TCP sockets to Neon Postgres without:
  1. Cloudflare Hyperdrive (which is optimized for connection pooling but has specific driver constraints), or
  2. A WebSocket-to-TCP proxy bridge, which adds significant latency, architectural fragility, and protocol overhead.

### 2.3 Dependency Compilation and Native Extensions
- Key dependencies such as `pydantic-core`, `cryptography`, and `asyncpg` are compiled C/Rust extensions.
- Running them on Workers requires compiling specialized WebAssembly wheels. While Pyodide supports a subset of compiled packages, their bundle size balloons to >80 MB, easily exceeding Cloudflare's 25 MB free upload ceiling.

---

## 3. The Approved Role: Cloudflare Workers as Edge Proxy / WAF

While disqualified as the full backend compute host, Cloudflare Workers is **superbly suited as an Edge Proxy / WAF**:

```javascript
// cloudflare_edge_proxy.js
export default {
  async fetch(request, env) {
    const clientIP = request.headers.get("CF-Connecting-IP");
    
    // 1. Edge Rate Limiting (100 req/min per IP)
    const { success } = await env.RATE_LIMITER.limit({ key: clientIP });
    if (!success) {
      return new Response("Too Many Requests", { status: 429, headers: { "Retry-After": "60" } });
    }

    // 2. Validate Telegram Webhook Secret Token at Edge
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/v1/telegram/webhook")) {
      const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
      if (secret !== env.TELEGRAM_WEBHOOK_SECRET) {
        return new Response("Unauthorized", { status: 403 });
      }
    }

    // 3. Proxy to Backend Container on Cloud Run
    return fetch(env.BACKEND_CONTAINER_URL + url.pathname + url.search, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
  }
};
```
- **Benefits**: Protects backend compute from DDoS attacks, filters unauthorized webhook requests in <5 ms, terminates TLS, and enforces IP rate limits with zero credit card risk.
