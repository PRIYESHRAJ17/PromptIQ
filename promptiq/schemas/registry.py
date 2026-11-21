"""Model and Environment Registry schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ModelRecordSchema(BaseModel):
    id: str
    provider: str
    model_id: str
    name: str
    context_window: int
    output_limit: int
    supports_tools: bool
    supports_structured_output: bool
    cutoff_date: str | None = None
    release_date: str | None = None
    is_zero_price: bool
    rate_limits: dict[str, Any]
    confidence: str
    verified_at: datetime | None = None
    source_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EnvironmentRecordSchema(BaseModel):
    id: str
    host: str
    surface: str
    supported_formats: list[str]
    manifest_schema: dict[str, Any]
    supported_tools: list[str]
    precedence_rules: list[str]
    verification_status: str
    last_verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
