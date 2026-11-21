"""Project Memory, Checkpoints, and Context Continuity schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CheckpointCreate(BaseModel):
    phase: str = Field(..., description="e.g. discovery_completed, initial_package_compiled, test_passed")
    summary: str
    verified_state: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class CheckpointResponse(BaseModel):
    id: str
    project_id: str
    phase: str
    summary: str
    verified_state: dict[str, Any]
    blockers: list[str]
    next_actions: list[str]
    files_snapshot: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContextPackRequest(BaseModel):
    """Request to compile and pack project context for an external agent or session."""

    target_environment: str = "google-antigravity"
    max_token_budget: int = 16000
    include_research: bool = True
    include_code_references: bool = True
    task_focus: str | None = Field(default=None, description="Optional topic or task focus for relevance weighting")
    priority_cutoff: str = Field(default="P2", description="Lowest priority requirement to include (P0, P1, P2, P3)")
    provenance_filter: list[str] | None = Field(default=None, description="Optional whitelist of provenances to include")


class ContextPackResponse(BaseModel):
    project_id: str
    constitution_version: int
    packed_context_markdown: str
    estimated_tokens: int
    items_included: list[str]
    items_truncated: list[str]
    latest_checkpoint: CheckpointResponse | None = None
