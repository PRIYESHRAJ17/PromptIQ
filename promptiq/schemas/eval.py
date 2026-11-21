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

    model_config = ConfigDict(from_attributes=True)
