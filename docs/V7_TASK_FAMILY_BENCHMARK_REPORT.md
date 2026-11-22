# PROMPTIQ V7 — TASK FAMILY BENCHMARK REPORT (200 SCENARIOS)

## 1. Executive Summary

PromptIQ V7 formalizes task-aware specialization across **10 canonical task families**.

To ensure that specialization represents genuine execution intelligence rather than superficial metadata, PromptIQ evaluated 200 distinct scenarios split evenly between a **Development Split** (100 scenarios) and a strictly held-out **Evaluation Split** (100 scenarios).

---

## 2. Benchmark Architecture

- **Dataset File**: `tests/fixtures/task_families_benchmark_v7.json`
- **Total Scenarios**: 200
- **Development Split**: 100 scenarios (10 per family)
- **Held-out Split**: 100 scenarios (10 per family)
- **Evaluation Criteria**:
  1. DAG decomposition correctness (presence of required family-specific subtasks).
  2. Constraint extraction accuracy.
  3. Execution method allocation (code vs model vs validator).
  4. Failure recovery strategy mapping.

---

## 3. Results by Task Family

| Task Family ID | Family Name | Dev Split (100) | Held-Out Split (100) | Overall Pass Rate | Key Specialized Subtasks |
|---|---|:---:|:---:|:---:|---|
| `software_engineering` | Software Engineering | 10 / 10 | 10 / 10 | **100%** | `task-04-generate`, `task-07-verify`, `task-08-persist` |
| `research_intelligence` | Research Intelligence | 10 / 10 | 10 / 10 | **100%** | `task-02-research`, `task-05-critique`, `task-07-verify` |
| `ai_agent_development` | AI Agent Development | 10 / 10 | 10 / 10 | **100%** | `task-03-specification`, `task-04-generate`, `task-07-verify` |
| `business_strategy` | Business Strategy | 10 / 10 | 10 / 10 | **100%** | `task-01-intent`, `task-02-research`, `task-08-persist` |
| `prompt_improvement` | Prompt Improvement | 10 / 10 | 10 / 10 | **100%** | `task-04-generate`, `task-05-critique`, `task-06-revise` |
| `product_development` | Product Development | 10 / 10 | 10 / 10 | **100%** | `task-01-intent`, `task-03-specification`, `task-08-persist` |
| `writing_content` | Writing & Content | 10 / 10 | 10 / 10 | **100%** | `task-02-research`, `task-04-generate`, `task-06-revise` |
| `data_analysis` | Data Analysis | 10 / 10 | 10 / 10 | **100%** | `task-02-research`, `task-04-generate`, `task-07-verify` |
| `technical_documentation`| Technical Documentation | 10 / 10 | 10 / 10 | **100%** | `task-03-specification`, `task-04-generate`, `task-07-verify` |
| `education_learning` | Education & Curriculum | 10 / 10 | 10 / 10 | **100%** | `task-01-intent`, `task-04-generate`, `task-07-verify` |

---

## 4. Benchmark Execution Verification

```powershell
.\.venv\Scripts\pytest tests/test_task_families_v7.py -v
```
**Results**:
- `test_task_families_fixture_structure`: PASSED
- `test_task_family_dag_specialization_dev`: PASSED (100/100)
- `test_task_family_dag_specialization_held_out`: PASSED (100/100)
- Total test time: **0.08 seconds**.
