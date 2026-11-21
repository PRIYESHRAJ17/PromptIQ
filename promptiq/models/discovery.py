"""Discovery session database models."""

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class DiscoverySession(Base, UUIDMixin, TimestampMixin):
    """Tracks state and captured context across conversational discovery turns."""

    __tablename__ = "discovery_sessions"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), default="software_project", nullable=False)
    depth: Mapped[str] = mapped_column(String(32), default="guided", nullable=False)  # quick, guided, deep

    # Structured responses and extracted context
    initial_intake: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extracted_facts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    current_stage: Mapped[str] = mapped_column(String(64), default="intake", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="discovery_sessions")
