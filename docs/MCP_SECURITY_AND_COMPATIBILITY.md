# PromptIQ Remote MCP Security & Transport Compatibility Specification

**Version**: 3.2.0  
**Specification**: Model Context Protocol (MCP) 2024-11 Streamable HTTP & SSE  
**Primary Endpoint**: `POST /api/v1/mcp`  
**Security Status**: HARDENED / VERIFIED  

---

## 1. Transport Architecture: Streamable HTTP as Primary

PromptIQ implements the official Model Context Protocol transport specification, designating **Streamable HTTP** as the primary protocol for containerized and serverless environments:

```
[MCP Client / External Agent]
              │
              │  HTTP POST /api/v1/mcp
              │  Headers:
              │    Authorization: Bearer <jwt>
              │    Origin: https://cursor.com
              │    Accept: text/event-stream (or application/json)
              ▼
    [Streamable HTTP Gateway]
              │
              ├── 1. Origin & Host Validation (DNS Rebinding Defense)
              ├── 2. Tenant JWT Verification
              ├── 3. Stateless JSON-RPC 2.0 Execution
              ▼
   [PromptIQ Core Services] (Discovery, Compiler, Autopsy, Memory)
              │
              ▼
[SSE Response Stream / JSON Response]
```

### Why Streamable HTTP is Primary for Cloud Native:
1. **Stateless Operations**: Serverless platforms (Google Cloud Run, AWS Fargate, Render) dynamically scale container instances. Legacy SSE pairs (`GET /sse` + `POST /messages`) rely on an in-memory session queue residing in a single container's RAM. If an incoming message routes to instance B while the SSE stream is open on instance A, messages drop. Streamable HTTP processes RPC calls statelessly on a single HTTP request/response cycle.
2. **DNS Rebinding & Origin Protection**: Web-based MCP clients (or malicious browser extensions) could attempt DNS rebinding to hijack local/cloud MCP servers. PromptIQ enforces `validate_mcp_origin`:
   - Checks the `Origin` and `Host` request headers against an approved whitelist.
   - Rejects untrusted origins with `HTTP 403 Forbidden`.
3. **Dual Content Negotiation**:
   - Clients requesting `Accept: text/event-stream` receive chunked Server-Sent Events (`data: {...}\n\n`).
   - Clients requesting `Accept: application/json` receive immediate synchronous JSON-RPC responses.

---

## 2. Legacy SSE Compatibility (`/sse` + `/messages`)

For backward compatibility with older MCP clients, PromptIQ retains the SSE endpoint pair with tenant isolation:
- `GET /api/v1/mcp/sse`: Establishes an SSE event stream and returns an endpoint URI with `sessionId`.
- `POST /api/v1/mcp/messages?sessionId=<uuid>`: Delivers JSON-RPC calls into the session queue.
- **Tenant Session Isolation**: Sessions are strictly bound to the authenticated user ID. Cross-tenant message injection is blocked with `TenantIsolationError` (HTTP 403).

---

## 3. Client Bridge Security & Scheme Validation

The `PromptIQClientBridge` (`promptiq.mcp.client_bridge`) establishes outbound connections to other MCP servers:
- **Strict Scheme Validation**: Rejects `file://`, `gopher://`, `ftp://`, or arbitrary local IPC sockets (mitigating Bandit B310 and SSRF vulnerabilities). Only `http://` and `https://` schemes are permitted.
- **Timeout Enforced**: 15-second bounded HTTP timeout on all bridge queries.
