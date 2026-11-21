"""Capacity Governor and Quota status schemas."""

from pydantic import BaseModel


class QuotaStatusResponse(BaseModel):
    provider: str
    is_paused: bool
    pause_reason: str | None = None
    minute_requests_used: int
    daily_requests_used: int
    user_requests_remaining_this_hour: int
    zero_price_policy_active: bool = True
    notice: str = "PromptIQ is 100% free. No user billing or API keys required."
