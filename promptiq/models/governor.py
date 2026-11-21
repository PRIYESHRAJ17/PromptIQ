"""Capacity Governor and Usage tracking database models."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class ProviderQuotaRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks upstream provider free tier quota consumption and pause state."""

    __tablename__ = "provider_quota_records"

    provider: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    minute_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minute_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pause_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class UsageRecord(Base, UUIDMixin, TimestampMixin):
    """Per-user fair-use consumption record."""

    __tablename__ = "usage_records"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)

    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requests_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tokens_estimated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
