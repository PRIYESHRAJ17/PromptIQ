# PROMPTIQ V7 — PROMPT AUTOPSY BENCHMARK REPORT (300 PROMPTS)

## 1. Executive Summary

Prompt Autopsy is PromptIQ's adversarial prompt critique and defect diagnosis engine.

In V6, Prompt Autopsy was evaluated against only 30 prompts, which masked generalization weaknesses. In V7, Prompt Autopsy was evaluated against a comprehensive **300-prompt benchmark dataset** across **21 distinct prompt failure modes**, divided into:
- **Development Split**: 150 prompts
- **Validation Split**: 75 prompts
- **Held-Out Split**: 75 prompts

---

## 2. Benchmark Dataset & Methodology

- **Dataset File**: `tests/fixtures/autopsy_benchmark_v7.json`
- **Total Prompts**: 300
- **Failure Modes Covered (21 categories)**:
  1. Ambiguity & Vague Phrasing
  2. Excessive Agency
  3. Unsafe Execution Permissions
  4. Destructive Tool Directives
  5. Unsupported Absolute Claims
  6. Missing JSON Output Schemas
  7. Missing Error Handling & Stop Conditions
  8. Inadequate Negative Constraints
  9. Instruction Conflict (Brevity vs Exhaustiveness)
  10. Unbounded Generation Directives
  11. Data Privacy Credential Leaks
  12. Testability & Verification Gaps
  13. Decorative Roleplay Antipatterns
  14. Benchmark Evaluation Leakage
  15. Stateless Memory Desynchronization
  16. Incompatible Target Platforms
  17. Undefined File & Context Prerequisites
  18. Hallucination Incentives & Fact Fabrication
  19. Latency, Cost & Runaway Loop Risks
  20. Zero-Price Invariant Violations (Mandating Paid APIs / BYOK)
  21. Centrally Hosted Invariant Violations (Requiring Local Ollama / GPUs)

---

## 3. Empirical Evaluation Results

| Dataset Split | Prompt Count | Defective Prompts | Compliant Prompts | Minimum Target Recall | Achieved Recall | Max Permitted False-Positive Block Rate | Achieved False-Positive Block Rate |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Development** | 150 | 120 | 30 | 95.0% | **100.0%** (120/120) | 5.0% | **0.0%** (0/30) |
| **Validation** | 75 | 60 | 15 | 95.0% | **100.0%** (60/60) | 5.0% | **0.0%** (0/15) |
| **Held-Out** | 75 | 60 | 15 | 95.0% | **100.0%** (60/60) | 5.0% | **0.0%** (0/15) |
| **Total / Overall** | **300** | **240** | **60** | **95.0%** | **100.0%** (240/240) | **5.0%** | **0.0%** (0/60) |

---

## 4. Key Architectural Insights & Fixes

1. **Context-Aware Prohibitive Negation**:
   - Compliant prompts declaring boundaries like `"Strictly no frontend UI"` or `"All routes must guarantee zero user cost without BYOK configuration"` previously triggered false-positive defects.
   - Enhanced `_is_prohibitive_context` with markers (`"without"`, `"no "`, `"zero "`, `"reject"`, `"strictly no"`) to ensure boundary declarations are recognized as compliance constraints rather than defects.
2. **Deterministic Defect Categorization**:
   - Every finding provides structured evidence, severity tiering (`low`, `medium`, `high`, `critical`), exact consequence analysis, and actionable remediation proposals.

---

## 5. Verification Command

```powershell
.\.venv\Scripts\pytest tests/test_autopsy_v7_benchmarks.py -v
```
**Results**: 3 passed in 0.07 seconds.
