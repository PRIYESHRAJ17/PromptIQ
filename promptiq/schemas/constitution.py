"""Project Constitution schemas with strict provenance tracking."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProvenanceType = Literal[
    "user_provided",
    "file_extracted",
    "connected_source",
    "inferred",
    "research_backed",
    "unknown",
    "conflicting",
]

RequirementPriority = Literal["P0", "P1", "P2", "P3"]
RequirementStatus = Literal["proposed", "confirmed", "rejected", "deferred"]


class RequirementItem(BaseModel):
    """An individual project requirement with provenance."""

    id: str = Field(..., description="Stable requirement identifier, e.g. REQ-AUTH-001")
    text: str = Field(..., description="Exact requirement statement")
    category: str = Field(default="functional", description="functional, non_functional, security, data, ux")
    priority: RequirementPriority = Field(default="P1")
    status: RequirementStatus = Field(default="confirmed")
    provenance: ProvenanceType = Field(default="user_provided")
    source_reference: str | None = Field(default=None, description="Originating document, turn, or citation")
    acceptance_criteria: str | None = Field(default=None, description="Observable pass/fail test condition")


class DecisionRecord(BaseModel):
    id: str
    decision: str
    alternatives_considered: list[str] = Field(default_factory=list)
    rationale: str
    owner: str = "user"
    date: str
    supersedes: str | None = None


class AssumptionRecord(BaseModel):
    id: str
    assumption: str
    risk: Literal["low", "medium", "high"] = "medium"
    status: Literal["active", "validated", "falsified"] = "active"


class OpenQuestionRecord(BaseModel):
    id: str
    question: str
    owner: str = "unassigned"
    status: Literal["open", "answered", "deferred"] = "open"


class UXSpecification(BaseModel):
    """Structured UX specification (Note: strictly requirements only; no frontend code)."""

    visual_direction: str | None = None
    brand_tokens: dict[str, Any] = Field(default_factory=dict)
    page_map: list[str] = Field(default_factory=list)
    screen_flows: list[dict[str, Any]] = Field(default_factory=list)
    accessibility_standards: list[str] = Field(default_factory=lambda: ["WCAG 2.1 AA"])
    responsive_breakpoints: list[str] = Field(default_factory=lambda: ["mobile", "tablet", "desktop"])
    theme_support: Literal["light_only", "dark_only", "both_system"] = "both_system"


class TechnicalDirection(BaseModel):
    preferred_stack: list[str] = Field(default_factory=list)
    prohibited_stack: list[str] = Field(default_factory=list)
    architecture_pattern: str = "modular_monolith"
    database_preference: str | None = None
    hosting_environment: str | None = None


class ConstitutionUpdate(BaseModel):
    goals: list[str] | None = None
    requirements: list[RequirementItem] | None = None
    scope_in: list[str] | None = None
    scope_out: list[str] | None = None
    ux_specs: UXSpecification | None = None
    technical_direction: TechnicalDirection | None = None
    decisions: list[DecisionRecord] | None = None
    assumptions: list[AssumptionRecord] | None = None
    open_questions: list[OpenQuestionRecord] | None = None


class ConstitutionApprovalRequest(BaseModel):
    approve: bool = Field(..., description="True to approve, False to reject")
    feedback: str | None = None


class ConstitutionResponse(BaseModel):
    id: str
    project_id: str
    version: int
    status: str
    is_approved: bool
    goals: list[str]
    requirements: list[RequirementItem]
    scope: dict[str, list[str]]
    ux_specs: dict[str, Any]
    technical_direction: dict[str, Any]
    decisions: list[DecisionRecord]
    assumptions: list[AssumptionRecord]
    open_questions: list[OpenQuestionRecord]
    diff_from_previous: dict[str, Any]
    approved_by_user_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConstitutionComparisonResponse(BaseModel):
    project_id: str
    v1: int
    v2: int
    diff: dict[str, Any]

