"""Prompt Test Lab and Benchmark evaluation schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCaseSchema(BaseModel):
    id: str
    description: str
    input_vars: dict[str, Any] = Field(default_factory=dict)
    expected_output_patterns: list[str] = Field(default_factory=list)
    assertion_type: str = "contains"  # contains, regex, schema_valid, not_contains


class EvaluationSuiteCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: str | None = None
    test_cases: list[EvaluationCaseSchema]


class EvaluationRunRequest(BaseModel):
    suite_id: str
    package_id: str
    model_id: str = "promptiq-mock-v1"


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

