"""Prompt Autopsy and Adversarial Critique schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CriticSeverity = Literal["critical", "high", "medium", "low", "info"]
CriticCategory = Literal[
    "ambiguity",
    "missing_requirements",
    "contradiction",
    "feasibility",
    "security",
    "output_contract",
    "context_overflow",
]
AutopsyVerdict = Literal["ready", "ready_with_caveats", "needs_revision", "blocked", "unsuitable"]


class CriticFindingSchema(BaseModel):
    category: CriticCategory
    severity: CriticSeverity
    finding: str
    evidence_passage: str | None = None
    consequence: str
    recommendation: str
    disposition: str = "pending"
    is_resolved: bool = False


class AutopsyRequest(BaseModel):
    prompt_text: str | None = Field(default=None, description="Pasted prompt text to diagnose")
    package_id: str | None = Field(default=None, description="Compiled package ID to critique")
    target_environment: str = Field(default="google-antigravity", description="Target host environment")


class AutopsyResponse(BaseModel):
    verdict: AutopsyVerdict
    summary: str
    findings: list[CriticFindingSchema]
    quality_scores: dict[str, float]  # static_quality, coverage, compatibility, security
    suggested_revision: str | None = None

    model_config = ConfigDict(from_attributes=True)
