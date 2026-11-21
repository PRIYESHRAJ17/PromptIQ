"""Critic Findings and Prompt Autopsy database model."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class CriticFinding(Base, UUIDMixin, TimestampMixin):
    """Structured critical review finding challenging assumptions, ambiguity, or errors."""

    __tablename__ = "critic_findings"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    package_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("prompt_packages.id"), nullable=True, index=True)

    category: Mapped[str] = mapped_column(String(64), nullable=False)  # ambiguity, contradiction, feasibility, security, output_contract
    severity: Mapped[str] = mapped_column(String(32), nullable=False)  # critical, high, medium, low, info

    finding: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_passage: Mapped[str | None] = mapped_column(Text, nullable=True)
    consequence: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disposition: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, accepted, rejected, deferred

    # Relationships
    package = relationship("PromptPackage", back_populates="critic_findings")
