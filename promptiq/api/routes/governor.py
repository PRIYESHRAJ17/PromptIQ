"""Capacity Governor and Service Status API routes."""

from fastapi import APIRouter

from promptiq.gateway.gateway import inference_gateway
from promptiq.schemas.governor import QuotaStatusResponse

router = APIRouter(prefix="/status", tags=["Status"])


@router.get("/capacity", response_model=QuotaStatusResponse)
async def get_capacity_status():
    """Inspect current zero-price inference capacity, rate limits, and pause states."""
    return inference_gateway.get_quota_status()
