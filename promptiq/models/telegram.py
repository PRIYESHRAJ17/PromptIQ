"""Telegram database models for durable webhook deduplication and state tracking."""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, DateTime

from promptiq.models.base import Base


class TelegramProcessedUpdate(Base):
    """Durable record of processed Telegram update IDs.

    Guarantees idempotency and prevents webhook retry replay across
    multiple server workers, process restarts, and container instances.
    """

    __tablename__ = "telegram_processed_updates"

    update_id = Column(BigInteger, primary_key=True, index=True)
    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
