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


@pytest.mark.asyncio
async def test_quota_ledger_and_idempotency(db_session: AsyncSession):
    """Verifies QuotaLedgerEntry recording, idempotency deduplication, and stale pruning."""
    import uuid
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from promptiq.models.governor import QuotaLedgerEntry, QuotaReservationRecord
    from promptiq.models.user import User, Workspace

    # Setup user and workspace
    user_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"quota_{user_id[:8]}@promptiq.dev",
        hashed_password="pw",
        full_name="Quota User",
    )
    db_session.add(user)
    await db_session.flush()

    ws = Workspace(id=ws_id, name="Quota WS", owner_id=user_id)
    db_session.add(ws)
    await db_session.flush()

    gov = CapacityGovernor(auto_load=False)
    model_id = "openai/gpt-oss-120b"
    idem_key = f"idem-{uuid.uuid4()}"

    # 1. Reserve quota with idempotency key
    t1 = await gov.reserve_quota_db(
        db=db_session,
        model_id=model_id,
        estimated_tokens=1500,
        ttl_seconds=60.0,
        user_id=user_id,
        workspace_id=ws_id,
        idempotency_key=idem_key,
    )

    # Calling again with same idempotency key returns same token
    t2 = await gov.reserve_quota_db(
        db=db_session,
        model_id=model_id,
        estimated_tokens=1500,
        ttl_seconds=60.0,
        user_id=user_id,
        workspace_id=ws_id,
        idempotency_key=idem_key,
    )
    assert t1 == t2

    # Verify QuotaLedgerEntry has RESERVED entry
    stmt = select(QuotaLedgerEntry).where(QuotaLedgerEntry.idempotency_key == idem_key)
    res = await db_session.execute(stmt)
    entry = res.scalar_one_or_none()
    assert entry is not None
    assert entry.status == "RESERVED"
    assert entry.tokens == 1500

    # 2. Commit quota
    await gov.commit_quota_db(
        db=db_session,
        token=t1,
        actual_tokens=1200,
        http_status=200,
        provider_request_id="req_test_quota_123",
        usage_kind="PROVIDER_REPORTED",
    )

    # Verify committed ledger entry exists
    stmt2 = select(QuotaLedgerEntry).where(
        QuotaLedgerEntry.idempotency_key == idem_key,
        QuotaLedgerEntry.status == "COMMITTED",
    )
    res2 = await db_session.execute(stmt2)
    committed_entry = res2.scalar_one_or_none()
    assert committed_entry is not None
    assert committed_entry.tokens == 1200
    assert committed_entry.provider_request_id == "req_test_quota_123"

    # 3. Test stale reservation pruning
    stale_rec = QuotaReservationRecord(
        token=f"res_stale_{uuid.uuid4().hex[:8]}",
        model_id=model_id,
        tokens=500,
        status="active",
        user_id=user_id,
        workspace_id=ws_id,
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    db_session.add(stale_rec)
    await db_session.flush()

    pruned = await gov.prune_stale_reservations_db(db=db_session)
    assert pruned >= 1

    await db_session.refresh(stale_rec)
    assert stale_rec.status == "expired"
