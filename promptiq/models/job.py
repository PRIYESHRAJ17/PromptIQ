"""Workflow and background job database models."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class WorkflowJob(Base, UUIDMixin, TimestampMixin):
    """Durable workflow execution record for long-running asynchronous jobs."""

    __tablename__ = "workflow_jobs"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=True, index=True
    )

    operation_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # collaboration, discovery, compilation, autopsy, eval, research
    status: Mapped[str] = mapped_column(
        String(32), default="QUEUED", nullable=False, index=True
    )  # QUEUED, RUNNING, PAUSED, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, CANCELLED

    current_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    execution_provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    checkpoint_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    lease_owner: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    workspace = relationship("Workspace")
    project = relationship("Project")
