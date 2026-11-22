# PROMPTIQ V7 — MODEL GATEWAY & ZERO-PRICE GOVERNANCE REPORT

## 1. Executive Summary

PromptIQ operates exclusively as a **centrally managed, zero-price hosted intelligence service**.

Users are never asked for API keys (no BYOK), and no paid inference routes exist in the system. The model gateway (`promptiq/gateway/gateway.py`) routes requests exclusively through centrally managed zero-price tiers with fair-use sliding-window rate limiting.

---

## 2. Invariant Enforcement & Governance

### 2.1 Zero-Price Invariant
- Any route with a non-zero price per token is strictly rejected at the schema and gateway level.
- Fallback routes that fall into paid tiers are prohibited.
- When hosted quota is exhausted, the gateway triggers `CapacityExhaustedError` with a calculated `retry_after` duration, pausing or queuing requests rather than switching to paid APIs.

### 2.2 Fair-Use Capacity Governor
The `CapacityGovernor` (`promptiq/gateway/governor.py`) enforces:
- Sliding 1-hour window per user ID (`RATE_LIMIT_USER_REQUESTS_PER_HOUR = 60`).
- System and internal autonomous agent tasks use dedicated or exempted system identifiers to avoid starvation.
- Pruning of expired timestamps to maintain $O(1)$ memory overhead.

---

## 3. Telemetry & Accounting

Every gateway inference call logs:
- `provider`: Hosted provider identifier.
- `model`: Exact model version string.
- `tokens_used`: Input tokens, completion tokens, and total token count.
- `duration_ms`: Network roundtrip and generation latency in milliseconds.
- `provenance`: Model execution provenance (`real`, `simulated`, or `mocked`).

---

## 4. Verification Evidence

- `tests/test_model_gateway.py` (all tests passing).
- `tests/test_agent_loop.py` (verified zero paid calls invoked during autonomous agent loop execution).
