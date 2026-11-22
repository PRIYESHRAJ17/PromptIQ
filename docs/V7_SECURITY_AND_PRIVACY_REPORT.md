# PROMPTIQ V7 — SECURITY, PRIVACY & DEFENSE-IN-DEPTH REPORT

## 1. Executive Summary

PromptIQ V7 enforces defense-in-depth across input sanitization, network requests, filesystem tools, tenant isolation, and credential protection.

---

## 2. Core Security Controls

### 2.1 SSRF Protection (31/31 Vectors Blocked)
The `validate_and_sanitize_url` function (`promptiq/core/security.py`) enforces strict network boundary controls:
- DNS resolution checks: Resolves domain to IP before connection.
- Private and loopback IP blocking: Blocks IPv4 (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`) and IPv6 loopback/link-local (`::1`, `fe80::/10`).
- Cloud metadata service blocking: Blocks AWS/GCP/Azure link-local metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- Scheme restriction: Only `http://` and `https://` permitted (blocks `file://`, `gopher://`, `ftp://`).
- Obfuscated IP protection: Rejects octal, hexadecimal, and dword IP notations.

### 2.2 Filesystem Path Traversal Protection
All filesystem tools (`filesystem_read`, `filesystem_write`) enforce:
- Canonical path resolution via `Path.resolve()`.
- Root path containment: Verifies that the resolved path is a subpath of `Path.cwd().resolve()` or `context["allowed_root"]`.
- Throws `PermissionError` on any attempt to escape via `../` or absolute root paths.

### 2.3 Row-Level Tenant Isolation
- Every database query in services filters by `workspace_id` and `user_id`.
- Foreign key relations link project constitutions, packages, and audit logs to the tenant workspace.
- Cross-tenant access attempts immediately raise `NotFoundError` or `PermissionDeniedError`.

### 2.4 Credential & Secret Protection
- Secrets, tokens, and hashed passwords are excluded from serialization schemas (`Field(exclude=True)`).
- Audit logs redact payload tokens and authorization headers.

---

## 3. Static Security Analysis (Bandit & Pip-Audit)

- **Bandit Static Analysis**: `bandit -r promptiq` reports **0 findings** (High/Medium/Low).
- **Pip-Audit**: `pip-audit` reports **0 known vulnerabilities**.
