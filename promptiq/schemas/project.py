"""Workspace and Project schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    visibility: str = Field(default="private", pattern="^(private|workspace|shared)$")


class ProjectCreate(ProjectBase):
    workspace_id: str | None = None  # If omitted, assigned to user's default workspace


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None


class ProjectResponse(ProjectBase):
    id: str
    workspace_id: str
    created_by_user_id: str
    current_constitution_version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
