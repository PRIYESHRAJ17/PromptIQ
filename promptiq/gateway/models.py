"""Gateway data transfer models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GatewayMessage(BaseModel):
    role: str = "user"  # system, user, assistant
    content: str


class InferenceRequest(BaseModel):
    """Internal gateway inference request."""

    messages: list[GatewayMessage] = Field(default_factory=list)
    system_instruction: str | None = None
    response_schema: dict[str, Any] | None = None
    max_tokens: int = 4096
    temperature: float = 0.2
    task_context: str = "general"
    target_model_id: str | None = None

    # User identification for capacity governance
    user_id: str = "system"
    workspace_id: str = "system"


class InferenceResponse(BaseModel):
    """Internal gateway inference response."""

    text: str
    structured_data: dict[str, Any] | list[Any] | None = None
    model_id: str
    provider: str
    latency_ms: float = 0.0
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    route_cost: float = 0.0  # MUST ALWAYS BE 0.0 under zero-price invariant
    request_id: str | None = None
    http_status: int = 200
    rate_limit_headers: dict[str, Any] | None = None
    request_timestamp: str | None = None
    response_timestamp: str | None = None

    model_config = ConfigDict(from_attributes=True)
