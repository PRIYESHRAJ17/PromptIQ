"""Project Memory, Checkpoints, and Artifact database models."""

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class Checkpoint(Base, UUIDMixin, TimestampMixin):
    """Verified snapshot of project milestone state, blockers, and next actions."""

    __tablename__ = "checkpoints"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    phase: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    verified_state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    blockers: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    next_actions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    files_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="checkpoints")


class Artifact(Base, UUIDMixin, TimestampMixin):
    """Uploaded reference document, source code, screenshot, or generated deliverable."""

    __tablename__ = "artifacts"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # doc, code, image, archive
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
