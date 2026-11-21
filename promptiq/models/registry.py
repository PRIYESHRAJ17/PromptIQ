"""Model and Environment Registry database models."""

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class ModelRegistryEntry(Base, UUIDMixin, TimestampMixin):
    """Catalog of supported AI models with verified capabilities and pricing status."""

    __tablename__ = "model_registry"

    provider: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    context_window: Mapped[int] = mapped_column(Integer, default=32768, nullable=False)
    output_limit: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)

    supports_tools: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_structured_output: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    cutoff_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    release_date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_zero_price: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rate_limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    confidence: Mapped[str] = mapped_column(
        String(32), default="provider_documented", nullable=False
    )
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class EnvironmentRecord(Base, UUIDMixin, TimestampMixin):
    """Catalog of host execution environments and native plugin conventions."""

    __tablename__ = "environment_registry"

    host: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    surface: Mapped[str] = mapped_column(String(64), nullable=False)  # cli, ide, web, agent

    supported_formats: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    manifest_schema: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    supported_tools: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    precedence_rules: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    verification_status: Mapped[str] = mapped_column(String(32), default="tested", nullable=False)
    last_verified_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
