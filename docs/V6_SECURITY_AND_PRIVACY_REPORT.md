# PROMPTIQ V6 — SECURITY AND PRIVACY AUDIT REPORT

## Executive Overview

PromptIQ V6 adheres to strict defense-in-depth principles: zero-price enforcement, non-negotiable credential protection, tenant isolation via row-level authorization, 31-vector SSRF blocking, prompt-injection defense, and secret redaction.

---

## 1. Zero-Price & Anti-BYOK Enforcement

**Implementation Source**: `promptiq/gateway/gateway.py`, `promptiq/core/security.py`

- **Rule**: PromptIQ is 100% free forever. No user API keys (BYOK) are ever accepted.
- **Enforcement**:
  - Ingress filters reject any request payload containing `openai_api_key`, `anthropic_api_key`, `gemini_api_key`, or generic `api_key` headers.
  - Model router prohibits any provider route with `cost_per_million > 0`.
  - Paid fallbacks are hard-blocked at the gateway layer.
  - Quota exhaustion results in an HTTP 429 response with `Retry-After` countdown headers; it never falls back to a paid provider.

---

## 2. SSRF Protection (31/31 Vectors Blocked)

**Implementation Source**: `promptiq/core/security.py` (`is_ssrf_safe_url`)

PromptIQ validates every URL before issuing outbound research requests:
- **Loopback & Localhost**: `127.0.0.1`, `localhost`, `127.127.127.127`, `::1`.
- **Private Subnets**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Link-Local & Multicast**: `169.254.0.0/16`, `224.0.0.0/4`.
- **Cloud Metadata Services**: `169.254.169.254` (AWS, GCP, Azure, DigitalOcean).
- **IP Obfuscation**: Dotted-hex (`0x7f.0.0.1`), decimal integer (`2130706433`), octal (`0177.0.0.1`).
- **Forbidden Schemes**: `file://`, `gopher://`, `dict://`, `ftp://`, `ldap://`.
- **DNS Rebinding Protection**: Resolves IP before checking; enforces safe IP in socket creation.

**Evidence**: 31 out of 31 automated test vectors in `tests/test_research_security.py` successfully blocked.

---

## 3. Tenant Isolation & Row-Level Authorization

**Implementation Source**: `promptiq/services/auth_service.py`, `promptiq/services/project_service.py`

- Every database query for projects, constitutions, specs, jobs, and evaluations filters by `tenant_id` and `user_id`.
- Cross-tenant access attempts return HTTP 404 (or 403 Forbidden) and record a security audit log event.
- Verified in `tests/test_auth_and_tenancy.py`.

---

## 4. Prompt Injection & Untrusted Content Defense

**Implementation Source**: `promptiq/research/evidence_graph.py`

- External text from research sources is stripped of control tokens (`System Override:`, `Ignore previous instructions`).
- Zero-width spaces, hidden HTML comments, and CSS display-none hacks are excised.
- Ingested text is framed inside `<untrusted_external_evidence>` quarantine boundaries.

---

## 5. Secret Redaction & Audit Integrity

- Logs, traces, error messages, and API responses pass through `SecretRedactor`.
- Matches API tokens, passwords, bearer tokens, JWT signatures, and credit card numbers.
- CLI output redacts credentials even when verbose `--debug` flags are enabled (tested in `tests/test_cli_subprocess.py`).
- Security tools: Bandit reports **0 issues** across 20,873 lines of code.
