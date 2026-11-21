"""Audit events and integration installations database models."""

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class AuditEvent(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail of cross-surface actions, approvals, and mutations."""

    __tablename__ = "audit_events"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    action: Mapped[str] = mapped_column(String(128), nullable=False)
    surface: Mapped[str] = mapped_column(String(64), nullable=False)  # web, telegram, mcp, cli, sdk
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # Redacted parameters


class IntegrationInstallation(Base, UUIDMixin, TimestampMixin):
    """Authorized external integration installation (e.g. MCP client, CLI key)."""

    __tablename__ = "integration_installations"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    target_host: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # antigravity, cursor, claude, codex
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    permissions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
