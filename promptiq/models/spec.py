"""PromptIQ Prompt Specification (PPS) database model."""

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class PromptSpecification(Base, UUIDMixin, TimestampMixin):
    """Canonical intermediate representation (PPS) linking requirements to target packages."""

    __tablename__ = "prompt_specifications"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    constitution_version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Core PPS Sections
    intent: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    target_profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    requirements: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tools_and_permissions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    workflow: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    deliverables: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    output_contract: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    validation_plan: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="specs")
    packages = relationship("PromptPackage", back_populates="spec", cascade="all, delete-orphan")
