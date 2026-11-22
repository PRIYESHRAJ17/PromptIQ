"""Prompt Autopsy and Adversarial Critique schemas."""

import uuid
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
    "hallucination_risk",
    "instruction_conflict",
    "tone_misalignment",
    "unbounded_generation",
    "missing_error_handling",
    "inadequate_constraints",
    "target_incompatibility",
    "over_specification",
    "under_specification",
    "testability_gap",
    "data_privacy_leak",
    "anti_pattern_roleplay",
    "eval_leakage",
    "state_desynchronization",
]
AutopsyVerdict = Literal["ready", "ready_with_caveats", "needs_revision", "blocked", "unsuitable"]


class CriticFindingSchema(BaseModel):
    id: str = Field(default_factory=lambda: f"FINDING-{uuid.uuid4().hex[:8]}")
    category: CriticCategory
    severity: CriticSeverity
    finding: str
    evidence_passage: str | None = None
    consequence: str
    recommendation: str
    disposition: str = "pending"
    is_resolved: bool = False
    blocks_release: bool = False
    verification_method: str = "deterministic_check"


class FindingResolution(BaseModel):
    finding_id: str
    status: Literal["resolved", "partially_resolved", "rejected_with_reason", "unresolved"]
    reason: str
    evidence: str | None = None


class AutopsyRevisionVerifyRequest(BaseModel):
    original_findings: list[CriticFindingSchema]
    revised_text: str
    expected_artifact_hash: str | None = None


class AutopsyRevisionVerifyResponse(BaseModel):
    all_resolved: bool
    blocks_release: bool
    resolutions: list[FindingResolution]
    resolved_count: int
    unresolved_count: int
    partially_resolved_count: int = 0
    has_contradictory_resolution: bool = False
    has_severity_escalation: bool = False
    artifact_hash: str | None = None
    expected_artifact_hash: str | None = None
    summary: str


class AutopsyRequest(BaseModel):
    prompt_text: str | None = Field(default=None, description="Pasted prompt text to diagnose")
    package_id: str | None = Field(default=None, description="Compiled package ID to critique")
    target_environment: str = Field(
        default="google-antigravity", description="Target host environment"
    )


class AutopsyResponse(BaseModel):
    verdict: AutopsyVerdict
    summary: str
    findings: list[CriticFindingSchema]
    quality_scores: dict[str, float]  # static_quality, coverage, compatibility, security
    suggested_revision: str | None = None

    model_config = ConfigDict(from_attributes=True)
