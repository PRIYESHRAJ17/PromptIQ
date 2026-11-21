"""Project Constitution database models."""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class ProjectConstitution(Base, UUIDMixin, TimestampMixin):
    """Authoritative, versioned source of truth for project requirements and specifications."""

    __tablename__ = "project_constitutions"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)  # draft, approved, archived
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Core structured sections
    goals: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    requirements: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    scope: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ux_specs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    technical_direction: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    decisions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    open_questions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    risks: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    conflicts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Change tracking
    diff_from_previous: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="constitutions")


class ConstitutionVersion(Base, UUIDMixin, TimestampMixin):
    """Immutable snapshot archive for auditability, version diffing, and rollback."""

    __tablename__ = "constitution_versions"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    diff: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
