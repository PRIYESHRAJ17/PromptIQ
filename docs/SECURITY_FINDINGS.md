# PromptIQ Security Findings and Remediation Ledger

## 1. Security Review Status
- **Current Security Status**: HARDENED & AUDITED (Zero Outstanding High/Critical Vulnerabilities)
- **Audit Policy**: Every external input is treated as untrusted data. Zero secrets in logs or packages. Hard zero-price gate. Complete tenant isolation.

---

## 2. Security Findings Log

| Finding ID | Severity | Category | File / Module | Description | Mitigation Implemented | Verification Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | CRITICAL | Secret Redaction | Logging & Serialization | Risk of logging sensitive JWT tokens or API secrets. | Implemented automated regex-based redaction filter in structured logging. | `tests/test_security_and_redaction.py` | RESOLVED |
| **SEC-002** | CRITICAL | Zero-Price Gate | Model Gateway | Risk of invoking billable routes or falling back to paid inference. | Hard eligibility gate checks pricing == 0; throws exception on any paid route. | `tests/test_zero_price_gateway.py` | RESOLVED |
| **SEC-003** | CRITICAL | Authentication & HMAC | `promptiq/api/routes/auth.py` | Telegram account link endpoint passed raw token instead of decoded user ID, bypassing HMAC check. | Added `verify_telegram_link_token` call before invoking `AuthService.link_telegram_account`. | `tests/test_auth_and_tenancy.py::test_telegram_link_api_endpoint` | RESOLVED |
| **SEC-004** | MAJOR | Multi-Tenancy & Authorization | `promptiq/api/routes/compiler.py` | Package export endpoint did not verify user workspace access to project ID. | Added mandatory `ProjectService.get_project(db, project_id, user.id)` authorization gate. | `tests/test_cross_surface_sync.py` | RESOLVED |
| **SEC-005** | MAJOR | Multi-Tenancy Isolation | `promptiq/eval/test_lab.py` | Evaluation run queried suite and package without filtering by `project_id`, enabling cross-tenant probing. | Enforced `project_id` matching on both `EvaluationSuite` and `PromptPackage` lookups. | `tests/test_eval_lab.py::test_evaluation_lab_execution_and_assertions` | RESOLVED |
| **SEC-006** | MAJOR | Webhook Authorization | `promptiq/api/routes/telegram.py` | Telegram webhook endpoint lacked validation for `X-Telegram-Bot-Api-Secret-Token`. | Configured `TELEGRAM_WEBHOOK_SECRET` header verification returning 403 on invalid tokens. | `promptiq/api/routes/telegram.py` | RESOLVED |
| **SEC-007** | MEDIUM | BYOK Prevention | `promptiq/gateway/eligibility.py` | `check_and_reject_byok` only recursed dictionaries, failing to inspect lists of dicts containing prohibited keys. | Implemented full recursive traversal for both nested dictionaries and lists of arbitrary depth. | `tests/test_zero_price_gateway.py::test_prohibited_byok_rejection` | RESOLVED |
| **SEC-008** | HIGH | Prompt Injection Guard | `promptiq/critic/autopsy.py` | Direct prompt injection phrases (e.g. system prompt overrides) executing unconstrained. | Prompt Autopsy heuristic inspection detects injection vectors and returns BLOCKED verdict. | `tests/test_critic_autopsy.py::test_prompt_autopsy_injection_blocking` | RESOLVED |
