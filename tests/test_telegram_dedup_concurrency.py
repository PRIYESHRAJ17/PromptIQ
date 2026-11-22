"""Stress and concurrency tests for Telegram webhook deduplication.

Verifies:
1. Concurrent duplicate updates (mass retry race condition) -> exactly 1 processed.
2. Concurrent independent updates -> all processed.
3. Multiple worker sessions / simulated multi-process.
4. Process restart resilience (new client instance detects past DB updates).
5. Corrupted persistence file tolerance (zero dependency on raw JSON file).
6. Multi-instance shared database synchronization.
"""

import asyncio
from datetime import datetime

import pytest
from conftest import TestSessionLocal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.models.telegram import TelegramProcessedUpdate
from promptiq.telegram.bot import TelegramBotClient, telegram_bot


@pytest.fixture(autouse=True)
async def cleanup_telegram_records(db_session: AsyncSession):
    telegram_bot.clear_deduplication_ledger()
    await telegram_bot.clear_deduplication_ledger_db(db_session)
    yield
    telegram_bot.clear_deduplication_ledger()
    await telegram_bot.clear_deduplication_ledger_db(db_session)


@pytest.mark.asyncio
async def test_concurrent_duplicate_updates_exactly_one_processed(db_session: AsyncSession, test_user):
    """Proves that 10 concurrent requests with the identical update_id yield exactly 1 processed."""
    user, _ = test_user
    chat_id = "concurrent_chat_1"
    update_id = 888001

    payload = {
        "update_id": update_id,
        "message": {
            "chat": {"id": chat_id},
            "text": "/start",
        },
    }

    # Simulate 10 simultaneous incoming webhook requests, each with its own DB session (standard FastAPI model)
    async def dispatch_request():
        async with TestSessionLocal() as session:
            return await telegram_bot.handle_update(session, payload)

    results = await asyncio.gather(*[dispatch_request() for _ in range(10)])

    processed = [r for r in results if r["status"] == "processed"]
    duplicates = [r for r in results if r["status"] == "duplicate_ignored"]

    assert len(processed) == 1, f"Expected exactly 1 processed, got {len(processed)}"
    assert len(duplicates) == 9, f"Expected 9 duplicate_ignored, got {len(duplicates)}"


@pytest.mark.asyncio
async def test_concurrent_independent_updates_all_processed(db_session: AsyncSession, test_user):
    """Proves that 10 concurrent distinct updates all process successfully."""
    user, _ = test_user
    chat_id = "concurrent_chat_2"

    async def dispatch_independent(i: int):
        payload = {
            "update_id": 888100 + i,
            "message": {
                "chat": {"id": chat_id},
                "text": f"/start distinct_{i}",
            },
        }
        async with TestSessionLocal() as session:
            return await telegram_bot.handle_update(session, payload)

    results = await asyncio.gather(*[dispatch_independent(i) for i in range(10)])

    processed = [r for r in results if r["status"] == "processed"]
    assert len(processed) == 10, f"Expected all 10 processed, got {len(processed)}"


@pytest.mark.asyncio
async def test_multi_session_worker_synchronization(db_session: AsyncSession, test_user):
    """Proves that separate database sessions (simulating multiple worker processes) coordinate deduplication."""
    update_id = 888201
    payload = {
        "update_id": update_id,
        "message": {
            "chat": {"id": "session_chat"},
            "text": "/start",
        },
    }

    # Worker A receives update in Session A
    async with TestSessionLocal() as session_a:
        res_a = await telegram_bot.handle_update(session_a, payload)
        assert res_a["status"] == "processed"
        await session_a.commit()

    # Worker B receives duplicate update in Session B (with fresh in-memory state)
    async with TestSessionLocal() as session_b:
        fresh_client = TelegramBotClient()
        res_b = await fresh_client.handle_update(session_b, payload)
        assert res_b["status"] == "duplicate_ignored"
        assert res_b["update_id"] == update_id


@pytest.mark.asyncio
async def test_process_restart_resilience(db_session: AsyncSession, test_user):
    """Proves that after a simulated server restart (clearing memory), duplicates are still caught from DB."""
    update_id = 888301
    payload = {
        "update_id": update_id,
        "message": {
            "chat": {"id": "restart_chat"},
            "text": "/start",
        },
    }

    # Process first update
    res1 = await telegram_bot.handle_update(db_session, payload)
    assert res1["status"] == "processed"
    await db_session.flush()

    # Simulate server process restart: create a new client with empty in-memory state
    restarted_bot = TelegramBotClient()
    assert update_id not in restarted_bot._processed_update_ids

    # Same update received after restart
    res2 = await restarted_bot.handle_update(db_session, payload)
    assert res2["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_corrupted_file_tolerance_and_zero_disk_dependency(db_session: AsyncSession, tmp_path, test_user):
    """Proves that database-backed deduplication is completely immune to disk corruption."""
    corrupted_file = tmp_path / "corrupted_telegram_updates.json"
    corrupted_file.write_text("{ INVALID_JSON_TRUNCATED_WRITE", encoding="utf-8")

    bot_with_corrupt_file = TelegramBotClient(dedup_path=str(corrupted_file))
    update_id = 888401

    payload = {
        "update_id": update_id,
        "message": {
            "chat": {"id": "corrupt_chat"},
            "text": "/start",
        },
    }

    # Should process without crashing despite corrupted file path
    res1 = await bot_with_corrupt_file.handle_update(db_session, payload)
    assert res1["status"] == "processed"

    # Should detect duplicate correctly
    res2 = await bot_with_corrupt_file.handle_update(db_session, payload)
    assert res2["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_multi_instance_shared_database_persistence(db_session: AsyncSession, test_user):
    """Proves that two distinct client instances coordinate state via the database."""
    client_east = TelegramBotClient()
    client_west = TelegramBotClient()
    update_id = 888501

    payload = {
        "update_id": update_id,
        "message": {
            "chat": {"id": "geo_chat"},
            "text": "/start",
        },
    }

    res_east = await client_east.handle_update(db_session, payload)
    assert res_east["status"] == "processed"

    # Client West should detect duplicate through the database
    res_west = await client_west.handle_update(db_session, payload)
    assert res_west["status"] == "duplicate_ignored"

    # Verify directly in database table
    stmt = select(TelegramProcessedUpdate).where(TelegramProcessedUpdate.update_id == update_id)
    rec = (await db_session.execute(stmt)).scalar_one_or_none()
    assert rec is not None
    assert rec.update_id == update_id
    assert isinstance(rec.processed_at, datetime)
