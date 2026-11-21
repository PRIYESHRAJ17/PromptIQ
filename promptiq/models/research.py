"""Research and Evidence Ledger database models."""

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class ResearchJob(Base, UUIDMixin, TimestampMixin):
    """Tracks research task scope, plan, execution state, and synthesized output."""

    __tablename__ = "research_jobs"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(
        String(32), default="deep", nullable=False
    )  # quick, decision, deep, benchmark
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    plan: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sources = relationship("SourceRecord", back_populates="job", cascade="all, delete-orphan")
    claims = relationship("EvidenceClaim", back_populates="job", cascade="all, delete-orphan")


class SourceRecord(Base, UUIDMixin, TimestampMixin):
    """Authoritative source record retrieved during research."""

    __tablename__ = "source_records"

    research_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_jobs.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # official_docs, paper, repo, analysis

    publication_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    retrieved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    locator: Mapped[str | None] = mapped_column(String(255), nullable=True)  # heading, line, page
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    job = relationship("ResearchJob", back_populates="sources")
    claims = relationship("EvidenceClaim", back_populates="source", cascade="all, delete-orphan")


class EvidenceClaim(Base, UUIDMixin, TimestampMixin):
    """Verified claim recorded in the Evidence Ledger."""

    __tablename__ = "evidence_claims"

    research_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_jobs.id"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_records.id"), nullable=False, index=True
    )

    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    support_status: Mapped[str] = mapped_column(
        String(32), default="verified", nullable=False
    )  # verified, contradicted, inferred, stale
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confidence_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    contrary_evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    job = relationship("ResearchJob", back_populates="claims")
    source = relationship("SourceRecord", back_populates="claims")
