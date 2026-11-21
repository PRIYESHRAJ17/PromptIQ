# Phase 3.4 Live Claims Audit & Formal Retraction
## Independent Audit of Claimed Empirical Live-Model Benchmarks

**Audit Date**: 2026-11-22  
**Auditor**: Antigravity Engineering Audit  
**Target Commit**: `e25f259`  
**Classification**: `FORMAL_RETRACTION` / `SYNTHETIC_RECLASSIFICATION`  

---

## 1. Executive Summary

The Phase 3.4 Delivery Report (`docs/PHASE_3_4_DELIVERY_REPORT.md`) claimed:
- An empirical 10-task benchmark was executed.
- Average quality score achieved was `0.922` with a `100%` pass rate.
- Configuration D (Dual-Model + Verifier) delivered an empirical `+13.5%` quality improvement over single-model generation.
- ₹0 inference cost was incurred under live accounts.

An independent audit of the source code (`promptiq/eval/pilot_benchmark.py`), runtime environment, execution logs, and network behavior reveals that **no live HTTP inference requests were transmitted to external provider endpoints during Phase 3.4**. The reported scores were generated from hardcoded deterministic scoring rubrics inside `pilot_benchmark.py`.

Therefore, the claim that Phase 3.4 demonstrated "empirical live-model performance" is **FORMALLY RETRACTED**. The scores are reclassified as **`SYNTHETIC` / `DETERMINISTIC`** design targets.

---

## 2. Forensic Investigation of Claimed 10-Task Benchmark

To satisfy Part 2 of the Phase 3.4.1 directive, each aspect of the claimed benchmark was forensically verified:

| # | Audit Question | Forensic Evidence & Code Finding | Verdict |
|---|---|---|---|
| **1** | **Was a real HTTP request sent?** | Code inspection of `promptiq/eval/pilot_benchmark.py:89-130` confirms `evaluate_pilot_suite()` iterates through `PILOT_CASES` without invoking `aiohttp`, `httpx`, `requests`, or any provider adapter. No network socket was opened. | **NO (0 requests sent)** |
| **2** | **Which provider received it?** | No provider endpoint (`api.groq.com` or `generativelanguage.googleapis.com`) received any HTTP payloads. | **NONE** |
| **3** | **Which exact model identifier was used?** | The identifiers `openai/gpt-oss-120b` and `openai/gpt-oss-20b` were referenced in configuration metadata, but were never transmitted to a live inference engine. | **METADATA ONLY** |
| **4** | **Was an actual API response received?** | No provider HTTP response headers or response bodies were received. | **NO** |
| **5** | **Is there a provider request ID?** | No provider-generated `x-request-id` or Groq/Google tracking ID exists in the logs or benchmark outputs. | **NONE** |
| **6** | **Is there a timestamp of a real network roundtrip?** | Timestamps in the report were static metadata or local CPU clock timestamps, not provider-measured latency. | **NO LIVE TIMESTAMPS** |
| **7** | **Is token usage recorded?** | No live token usage was returned by a provider API; values were estimated from synthetic word counts. | **NO PROVIDER TOKENS** |
| **8** | **Is the actual model response preserved?** | No raw model output strings from a live LLM exist in the benchmark runner artifacts. | **NO LIVE RESPONSES** |
| **9** | **Is there an independent evaluation record?** | Evaluation was purely deterministic logic inside Python unit fixtures. | **NO INDEPENDENT EVAL** |
| **10** | **Was the operation actually charged ₹0 under live accounts?** | Because zero network calls were dispatched, no billing occurred. However, zero-price billing was **not validated** on a live provider account. | **NOT VALIDATED ON LIVE ACCOUNT** |

---

## 3. Root Cause Analysis

Inspection of `promptiq/eval/pilot_benchmark.py:98-120` shows the exact source of the claimed numbers:

```python
# Lines 98-110 in promptiq/eval/pilot_benchmark.py
for case in PILOT_CASES:
    case_id = case["id"]
    cat = case["category"]

    # Config A: 120B alone (strong reasoning, high instruction adherence)
    score_a = 0.92
    # Config B: 20B alone (fast, slightly less nuanced on edge cases)
    score_b = 0.84
    # Config C: 120B gen + 20B critic (catches missing assumptions and ambiguities)
    score_c = 0.95
    # Config D: Gen + Critic + Deterministic Verification (100% invariant enforcement)
    score_d = 0.99
```

The script author intended to construct a benchmark harness and synthetic evaluation framework, but the delivery report conflated this synthetic harness with live empirical execution.

Furthermore, running the smoke test utility (`python -m promptiq.gateway.smoke_test --provider groq --opt-in`) in the current workspace immediately outputs:
```
Execution Result: BLOCKED_EXTERNAL
Success:          False
Error / Hold:     No operator credential configured for provider 'groq'. Classified as BLOCKED_EXTERNAL. Cannot make live network calls.
```

This confirms that live execution was never physically possible during the run because `GROQ_API_KEY` was not configured in the host environment.

---

## 4. Formal Score Reclassification

All benchmark figures reported in Phase 3.4 are hereby reclassified:

| Configuration | Phase 3.4 Claimed Status | Phase 3.4.1 Reclassified Status | True Nature of Metric |
|---|---|---|---|
| **Config A** (120B alone) | `LIVE_VERIFIED` (0.812) | **`SYNTHETIC` / `DETERMINISTIC`** | Modeled single-model baseline score rubric. |
| **Config B** (20B alone) | `LIVE_VERIFIED` (0.741) | **`SYNTHETIC` / `DETERMINISTIC`** | Modeled fast-model baseline score rubric. |
| **Config C** (120B Gen + 20B Critic) | `LIVE_VERIFIED` (0.884) | **`SYNTHETIC` / `DETERMINISTIC`** | Modeled dual-model consensus score rubric. |
| **Config D** (Gen + Critic + Verifier) | `LIVE_VERIFIED` (0.922, +13.5%) | **`SYNTHETIC` / `DETERMINISTIC`** | Modeled full-pipeline invariant enforcement target. |

### Historical Preservation:
These values are **preserved as synthetic baseline targets** and unit-test validation fixtures in `tests/` and `docs/`. They demonstrate that the deterministic verification algorithms function mathematically, but they must **never** be cited as evidence of live model inference quality until genuine HTTP requests with provider request IDs are captured.

---

## 5. Corrective Actions Enacted in Phase 3.4.1

1. **Separation of Harness from Live Results**: `promptiq/eval/pilot_benchmark.py` is explicitly documented as a synthetic scoring harness.
2. **Fail-Closed Live Guard**: Any call to live inference without valid operator credentials and confirmed free account status strictly returns `BLOCKED_EXTERNAL`.
3. **No Synthetic Masking**: Under no circumstances will synthetic or mock outputs be presented as live external execution.
4. **Mandatory Audit Ledger**: Every future live test must record HTTP status, roundtrip latency (ms), provider request ID, input/output tokens, and raw model output strings.
