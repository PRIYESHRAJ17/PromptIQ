"""Tests for Database-Backed Quota Governance, Reservations, and Reconciliations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.gateway.governor import CapacityGovernor


@pytest.mark.asyncio
async def test_quota_reservation_db_lifecycle(db_session: AsyncSession):
    """Verifies atomic reservation, DB persistence, and reconciliation."""
    gov = CapacityGovernor(auto_load=False)
    model_id = "openai/gpt-oss-120b"

    # 1. Reserve 1,000 tokens
    token = await gov.reserve_capacity_db(
        db=db_session,
        model_id=model_id,
        estimated_tokens=1000,
        ttl_seconds=30.0,
        user_id="user-123",
    )
    assert token.startswith("res_")

    # Verify governor sees reserved capacity
    status = gov.get_model_quota_status(model_id)
    assert status["reserved_tokens"] == 1000

    # 2. Reconcile with 850 actual tokens
    await gov.reconcile_reservation_db(
        db=db_session,
        token=token,
        actual_tokens=850,
        http_status=200,
    )

    # Reservation cleared from in-flight and recorded in usage
    status_after = gov.get_model_quota_status(model_id)
    assert status_after["reserved_tokens"] == 0
    assert status_after["tokens_last_minute"] == 850

    # 3. Release another reservation
    token2 = await gov.reserve_capacity_db(
        db=db_session,
        model_id=model_id,
        estimated_tokens=500,
    )
    released = await gov.release_reservation_db(db=db_session, token=token2)
    assert released is True

    status_final = gov.get_model_quota_status(model_id)
    assert status_final["reserved_tokens"] == 0
