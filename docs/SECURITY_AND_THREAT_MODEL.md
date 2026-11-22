# PromptIQ — Security Architecture and Threat Model

**Version**: 3.0.0  
**Updated**: 2026-11-22  
**Security Status**: HARDENED & AUDITED (Zero Outstanding High/Critical Findings)  
**SAST Results**: Bandit: 0 issues across 17,143 LOC | pip-audit: 0 known vulnerabilities  

---

## 1. Executive Summary

PromptIQ operates under a **Zero-Trust, Zero-Price, Read-Only Default** security posture. Every external input is treated as untrusted data, whether arriving via REST API, MCP tool calls, CLI arguments, Telegram webhooks, or external web search results.

This document formalizes the platform's threat model, security controls, cryptographic safeguards, and verification evidence across the full attack surface.

---

## 2. Threat Model (STRIDE & OWASP LLM Top 10)

| Threat Category | Potential Attack Vector | PromptIQ Mitigation Implemented | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Forged Telegram webhook updates or impersonated tenant identities. | Constant-time secret token check (`secrets.compare_digest`), cryptographically signed HMAC linking tokens, JWT signature validation. | `tests/test_telegram_bot.py`, `tests/test_auth_and_tenancy.py` |
| **Tampering** | Modification of Project Constitution history or prompt packages. | Canonical Project Constitution is versioned and append-only. Cryptographic content hashing (SHA-256) on all compiled packages. | `tests/test_constitution.py`, `promptiq/models/constitution.py` |
| **Repudiation** | Unaudited modifications to projects, discovery answers, or evaluations. | Comprehensive, append-only `AuditLog` records actor, action, timestamp, resource ID, and delta payload. | `promptiq/models/audit.py` |
| **Information Disclosure** | Secret leakage in logs; cross-tenant data probing (IDOR); cloud metadata exfiltration (SSRF). | Automated regex redaction in all logging sinks; strict workspace scoping in every DB query; socket-pinned SSRF blocking. | `tests/test_security_and_redaction.py`, `tests/test_research_security.py` |
| **Denial of Service** | Upstream provider quota exhaustion; infinite prompt evaluation loops; memory exhaustion. | `CapacityGovernor` durable token ledger with fail-closed circuit breaker; evaluation timeout limits; sliding-window rate limiters. | `tests/test_quota_reservation_transactions.py` |
| **Elevation of Privilege** | Container escape; execution of mutating shell commands; bypassing read-only sandbox. | Non-root Docker container (UID 10001); static analysis in acceptance suite strictly forbidding mutating shell/file tools in compiled agents. | `tests/test_acceptance_integrity_negative.py`, Dockerfile |
| **Prompt Injection (LLM01)** | System prompt override; jailbreaks; indirect injection via research search snippets. | Prompt Autopsy heuristic inspection detects injection vectors; research snippets sanitized before prompt injection. | `tests/test_critic_autopsy.py` |
| **Insecure Output (LLM02)** | Compiler output generating malicious execution code without warnings. | Adversarial autopsy critique; deterministic evaluation rubrics scoring safety and testability. | `tests/test_eval_lab.py` |
| **Supply Chain (LLM03)** | Vulnerable third-party Python packages. | Continuous `pip-audit` scanning against PyPI Advisory Database. Zero known vulnerabilities. | `pip-audit` report |
| **Model Theft / Accidental Spend** | Unexpected credit card billing; auto-upgrade from free to paid tiers. | Hard `ZeroPriceGate` rejecting any non-zero priced model, paid fallback, or user-provided billing key. | `tests/test_zero_price_gateway.py` |

---

## 3. Deep-Dive Security Controls

### 3.1 Socket-Pinned SSRF Defense
PromptIQ's `LiveSearchConnector` defeats Server-Side Request Forgery and DNS rebinding attacks:
- **Private Subnet Filtering**: Checks target IP against all RFC 1918, RFC 3927 (link-local), RFC 5737, and IPv6 unique local/link-local ranges.
- **Cloud Metadata Shield**: Explicitly blocks `169.254.169.254` (AWS/GCP/Azure metadata services).
- **Socket Pinning (`_pinned_getaddrinfo`)**: Pins the TCP connection to the validated IP, preventing TOCTOU DNS rebinding between hostname check and HTTP socket connection.
- **Empirical Test**: 31 diverse SSRF attack vectors validated and blocked in `tests/test_research_security.py`.

### 3.2 Tenant Isolation & IDOR Defense
Every database query in PromptIQ enforces strict multi-tenant authorization:
- `ProjectService.get_project(db, project_id, user_id)` verifies that the requesting user owns the workspace.
- Cross-tenant queries across Discovery sessions, Project Constitutions, Compiled Packages, Evaluations, and Quota allocations return HTTP 404/403.
- Validated exhaustively in `tests/test_auth_and_tenancy.py::test_exhaustive_cross_tenant_idor_enforcement`.

### 3.3 Zero-Price Gate & BYOK Prevention
PromptIQ enforces a strict zero-price invariant:
- Users cannot enter API keys (OpenAI, Anthropic, Gemini, Groq, OpenRouter).
- `check_and_reject_byok` recursively inspects all request payloads (dicts, lists, query parameters, headers) and rejects keys matching prohibited patterns.
- Model registry requires `pricing.prompt == 0.0` and `pricing.completion == 0.0`. Any model with non-zero pricing triggers `ZeroPriceViolationError` and fails closed.

### 3.4 Secret Redaction
All structured log handlers and JSON serializers pass through an automated secret filter:
- Patterns detected and replaced with `[REDACTED]`:
  - JWT Tokens: `eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+`
  - Bearer Tokens: `Bearer [a-zA-Z0-9_\-\.]{16,}`
  - API Keys: `gsk_[a-zA-Z0-9]{20,}`, `AIza[0-9A-Za-z-_]{35}`, `sk-[a-zA-Z0-9]{20,}`
- Verified in `tests/test_security_and_redaction.py`.

---

## 4. Static Analysis & Audit Evidence

### 4.1 Bandit Static Application Security Testing (SAST)
```text
Run started: 2026-11-22
Scanned Codebase: promptiq/
Total lines of code: 17,143
Issues identified: 0
Severity Breakdown:
  Critical: 0
  High: 0
  Medium: 0
  Low: 0
```
Status: **100% CLEAN (Zero findings)**.

### 4.2 Python Package Dependency Audit (`pip-audit`)
```text
No known vulnerabilities found
Scanned: all installed environment dependencies (.venv)
Status: CLEAN
```

---

## 5. Residual Risks & Ongoing Mitigations

| Risk | Impact | Likelihood | Mitigation |
| :--- | :--- | :--- | :--- |
| **Upstream Free Tier Policy Change** | Upstream provider (e.g. GroqCloud, Google AI Studio) discontinues or modifies free tier terms. | Low-Medium | `CapacityGovernor` detects rate limit changes dynamically; multiple redundant free-tier adapters exist; fail-closed behavior ensures zero surprise spend. |
| **Airgapped Environment Limitations** | Live search and live model inference unavailable in isolated networks. | High (in isolated CI) | Graceful fallback to deterministic mock evaluation and simulated research, clearly marked with audit warnings. |
| **Local File Quota Ledger Lock Contention** | Extremely high concurrent CLI process contention on Windows NTFS file locks. | Low | Lock retry loop with exponential backoff and randomized jitter (up to 5 retries over 500ms). |
