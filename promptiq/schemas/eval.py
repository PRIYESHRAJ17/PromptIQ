"""Prompt Test Lab and Benchmark evaluation schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EvaluationMethod = Literal[
    "deterministic",
    "schema_validation",
    "model_based",
    "evidence_grounding",
    "safety_boundary",
    "human_review",
]


class EvaluationCaseSchema(BaseModel):
    id: str
    description: str
    method: EvaluationMethod = "deterministic"
    input_vars: dict[str, Any] = Field(default_factory=dict)
    expected_output_patterns: list[str] = Field(default_factory=list)
    assertion_type: str = (
        "contains"  # contains, regex, schema_valid, not_contains, evidence_grounded
    )
    expected_schema: dict[str, Any] | None = None


class EvaluationSuiteCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: str | None = None
    test_cases: list[EvaluationCaseSchema]


class EvaluationRunRequest(BaseModel):
    suite_id: str
    package_id: str
    model_id: str = "promptiq-mock-v1"
    num_runs: int = Field(
        default=1, ge=1, le=10, description="Multi-run trial count for variance measurement"
    )


class EvaluationRunResponse(BaseModel):
    id: str
    suite_id: str
    package_id: str | None
    model_id: str
    pass_rate: float
    total_cases: int
    passed_cases: int
    results: list[dict[str, Any]]
    latency_ms: float | None = None
    cost_estimate: float = 0.0
    execution_mode: str = "mock"
    num_runs: int = 1
    mean_latency_ms: float | None = None
    latency_variance: float | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ComparativeRunResponse(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    baseline_pass_rate: float
    candidate_pass_rate: float
    pass_rate_delta: float
    has_regressions: bool
    newly_failed_cases: list[str] = Field(default_factory=list)
    newly_passed_cases: list[str] = Field(default_factory=list)
    latency_delta_ms: float = 0.0
    summary: str
