"""Compiled target prompt package database model."""

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class PromptPackage(Base, UUIDMixin, TimestampMixin):
    """Target-native compiled artifact bundle ready for execution or export."""

    __tablename__ = "prompt_packages"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    spec_id: Mapped[str] = mapped_column(String(36), ForeignKey("prompt_specifications.id"), nullable=False, index=True)

    target_environment: Mapped[str] = mapped_column(String(64), nullable=False)
    output_type: Mapped[str] = mapped_column(String(32), nullable=False)  # prompt_only, prompt_suite, complete_package

    manifest: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    files: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # path: content
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="packages")
    spec = relationship("PromptSpecification", back_populates="packages")
    critic_findings = relationship("CriticFinding", back_populates="package", cascade="all, delete-orphan")
