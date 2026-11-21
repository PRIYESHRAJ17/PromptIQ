"""Project and ProjectMembership database models."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    """Canonical Project entity shared across Web, Telegram, and Integrations."""

    __tablename__ = "projects"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Active/current version pointer for quick resolution
    current_constitution_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), default="private", nullable=False
    )  # private, workspace, shared

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    memberships = relationship(
        "ProjectMembership", back_populates="project", cascade="all, delete-orphan"
    )
    constitutions = relationship(
        "ProjectConstitution", back_populates="project", cascade="all, delete-orphan"
    )
    discovery_sessions = relationship(
        "DiscoverySession", back_populates="project", cascade="all, delete-orphan"
    )
    specs = relationship(
        "PromptSpecification", back_populates="project", cascade="all, delete-orphan"
    )
    packages = relationship("PromptPackage", back_populates="project", cascade="all, delete-orphan")
    checkpoints = relationship("Checkpoint", back_populates="project", cascade="all, delete-orphan")


class ProjectMembership(Base, UUIDMixin, TimestampMixin):
    """Permissions for users within a specific project."""

    __tablename__ = "project_memberships"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(32), default="editor", nullable=False
    )  # viewer, editor, admin

    # Relationships
    project = relationship("Project", back_populates="memberships")
