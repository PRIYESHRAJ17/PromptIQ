"""PromptIQ Prompt Specification (PPS) intermediate representation schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntentSchema(BaseModel):
    task_type: str = "software_project"
    primary_objective: str
    target_audience: str = "developers"
    success_criteria: list[str] = Field(default_factory=list)


class TargetProfileSchema(BaseModel):
    host: str = Field(..., description="e.g. google-antigravity, claude-code, cursor, openai-codex, gemini-cli")
    provider: str = Field(..., description="e.g. google, anthropic, openai")
    model_id: str = Field(..., description="e.g. gemini-3.8-flash, claude-3-7-sonnet, gpt-4o")
    route: str = Field(default="hosted_adapter", description="Access route")
    runtime_version: str | None = None
    tools_available: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class DeliverableItem(BaseModel):
    path: str
    format: str = "text/markdown"
    description: str


class OutputContractSchema(BaseModel):
    format: str = "markdown"
    sections_required: list[str] = Field(default_factory=list)
    rules_and_invariants: list[str] = Field(default_factory=list)
    manifest_required: bool = False


class PromptSpecSchema(BaseModel):
    """The canonical, strongly-typed intermediate representation (PPS)."""

    spec_version: str = "1.0.0"
    project_id: str
    constitution_version: int
    intent: IntentSchema
    target_profile: TargetProfileSchema
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    tools_and_permissions: dict[str, Any] = Field(default_factory=dict)
    workflow_phases: list[dict[str, Any]] = Field(default_factory=list)
    deliverables: list[DeliverableItem] = Field(default_factory=list)
    output_contract: OutputContractSchema
    validation_plan: dict[str, Any] = Field(default_factory=dict)
    provenance_trail: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
