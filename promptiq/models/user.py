"""User, Workspace, and Membership database models."""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User account entity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Telegram integration chat ID for cross-surface binding
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    # Relationships
    workspaces = relationship(
        "WorkspaceMembership", back_populates="user", cascade="all, delete-orphan"
    )


class Workspace(Base, UUIDMixin, TimestampMixin):
    """Workspace boundary for multi-tenancy and team collaboration."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    memberships = relationship(
        "WorkspaceMembership", back_populates="workspace", cascade="all, delete-orphan"
    )
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMembership(Base, UUIDMixin, TimestampMixin):
    """Associates a User with a Workspace and assigns a role."""

    __tablename__ = "workspace_memberships"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(32), default="member", nullable=False
    )  # owner, admin, member

    # Relationships
    workspace = relationship("Workspace", back_populates="memberships")
    user = relationship("User", back_populates="workspaces")
