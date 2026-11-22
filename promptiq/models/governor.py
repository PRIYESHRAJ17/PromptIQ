"""Capacity Governor and Usage tracking database models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
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

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )

    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requests_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tokens_estimated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class QuotaReservationRecord(Base, UUIDMixin, TimestampMixin):
    """Database-backed transactional quota reservation record."""

    __tablename__ = "quota_reservations"

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="active", nullable=False
    )  # active, reconciled, released, expired
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    actual_tokens_consumed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuotaLedgerEntry(Base, UUIDMixin, TimestampMixin):
    """Database-backed distributed quota ledger entry for multi-instance deployments."""

    __tablename__ = "quota_ledger_entries"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    usage_kind: Mapped[str] = mapped_column(
        String(32), default="PROVIDER_REPORTED", nullable=False
    )  # ESTIMATED, PROVIDER_REPORTED, UNKNOWN
    status: Mapped[str] = mapped_column(
        String(32), default="COMMITTED", nullable=False
    )  # RESERVED, COMMITTED, RELEASED, EXPIRED
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
