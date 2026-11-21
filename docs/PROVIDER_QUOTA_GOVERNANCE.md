# PromptIQ Provider Quota Governance & Rate Limit Specification

**Version**: 3.2.0  
**Engine**: `CapacityGovernor` (`promptiq.gateway.governor`)  
**Status**: ACTIVE / HARDENED  

---

## 1. Multi-Tiered Quota Governance Architecture

The PromptIQ Capacity Governor implements a layered defense against provider throttling, rate exhaustion, and billable leakage:

```
[Incoming Request]
        │
        ▼
[Layer 1: User Fair-Use Gate] ─────────► Sliding 1-hour window (default: 60 req/hr)
        │
        ▼
[Layer 2: Concurrency Semaphore] ──────► Global concurrency limit (default: 10 parallel)
        │
        ▼
[Layer 3: Provider Circuit Breaker] ───► Evaluates provider pause state (tripped by upstream 429)
        │
        ▼
[Layer 4: Model-Specific Quotas] ──────► Enforces model RPM, RPD, TPM, and TPD ceilings
        │
        ▼
[Layer 5: Header Inspection] ──────────► Parses upstream rate limit and retry headers
        │
        ▼
[Layer 6: Fail-Closed Zero-Price Gate] ─► $0/token verification; rejects non-zero routes
```

---

## 2. Model-Specific Free-Tier Quota Ledger

| Model ID | Provider | RPM | RPD | TPM | TPD | Critical Threshold |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`gemini-3.8-flash`** | Google AI Studio | 15 | 1,500 | 1,000,000 | 10,000,000 | Throttles on 15 RPM |
| **`gemini-3.5-flash-lite`** | Google AI Studio | 30 | 1,500 | 1,000,000 | 10,000,000 | Throttles on 30 RPM |
| **`gemini-2.5-flash`** | Google AI Studio | 15 | 1,500 | 1,000,000 | 10,000,000 | Throttles on 15 RPM |
| **`openai/gpt-oss-120b`** | GroqCloud | 30 | 1,000 | 8,000 | 100,000 | **Strict daily ceiling: 1,000 RPD or 100k TPD** |
| **`openai/gpt-oss-20b`** | GroqCloud | 30 | 14,400 | 6,000 | 500,000 | High-volume burst route (14,400 RPD) |
| **`qwen/qwen3.8-27b`** | GroqCloud | 30 | 1,000 | 6,000 | 100,000 | Daily coding ceiling: 100k TPD |
| **`promptiq-mock-v1`** | Internal Engine | 10,000 | 1,000,000 | 10,000,000 | 100,000,000 | Unlimited local/CI test harness |

---

## 3. Upstream Header Inspection

`CapacityGovernor.inspect_response_headers` continuously extracts real-time rate limit telemetry from provider HTTP responses:

1. **`retry-after` Header**:
   - Encountered on HTTP 429 status codes.
   - Extracts seconds to pause; trips the provider circuit breaker for `max(5, retry_after)` seconds.
2. **`x-ratelimit-remaining-requests` Header**:
   - If remaining requests reaches `0`, trips circuit breaker for 60 seconds (or duration of `x-ratelimit-reset-requests`).
3. **`x-ratelimit-remaining-tokens` Header**:
   - If remaining token headroom falls below `500 tokens`, proactively trips circuit breaker for 30 seconds to prevent mid-turn request truncation.
