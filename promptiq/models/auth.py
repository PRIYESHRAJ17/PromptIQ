"""Token revocation and session lifecycle database models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class RevokedToken(Base, UUIDMixin, TimestampMixin):
    """Blocklist of invalidated or logged-out JWT access tokens."""

    __tablename__ = "revoked_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """Durable refresh tokens for session renewal and rotation."""

    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    rotated_to_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
