"""Pydantic schemas for durable workflow background jobs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    """Payload to initiate a durable background workflow job."""

    operation_type: str = Field(..., description="Type of operation (collaboration, autopsy, etc.)")
    project_id: str | None = Field(default=None, description="Optional associated project ID")
    idempotency_key: str | None = Field(default=None, description="Client idempotency key")
    initial_stage: str = Field(default="initialization", description="Starting stage name")
    checkpoint_data: dict[str, Any] = Field(default_factory=dict, description="Initial checkpoint state")


class JobStageRecord(BaseModel):
    """Historical stage record in workflow execution."""

    stage: str
    status: str
    timestamp: str
    progress_percent: int | None = None
    details: dict[str, Any] | None = None


class JobResponse(BaseModel):
    """Standardized representation of a workflow job."""

    id: str
    user_id: str
    workspace_id: str
    project_id: str | None = None
    operation_type: str
    status: str
    current_stage: str | None = None
    stage_history: list[dict[str, Any]] = Field(default_factory=list)
    progress_percent: int = 0
    execution_provenance: dict[str, Any] = Field(default_factory=dict)
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)
    result_data: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    failure_reason: str | None = None
    fencing_token: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JobCancelRequest(BaseModel):
    """Payload to request job cancellation."""

    reason: str = Field(default="Cancelled by user", description="Reason for cancellation")
