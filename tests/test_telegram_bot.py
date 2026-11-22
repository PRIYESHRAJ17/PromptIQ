"""Test Telegram Bot companion, commands, and conversational intake."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.security import generate_telegram_link_token
from promptiq.telegram.bot import telegram_bot


@pytest.fixture(autouse=True)
async def reset_telegram_dedup(db_session: AsyncSession):
    telegram_bot.clear_deduplication_ledger()
    await telegram_bot.clear_deduplication_ledger_db(db_session)
    yield
    telegram_bot.clear_deduplication_ledger()
    await telegram_bot.clear_deduplication_ledger_db(db_session)


@pytest.mark.asyncio
async def test_telegram_start_and_account_linking(db_session: AsyncSession, test_user):
    """Tests /start onboarding and account linking via HMAC token."""
    user, _ = test_user
    chat_id = "987654321"

    # 1. First start without token (unlinked welcome)
    update_guest = {
        "message": {
            "chat": {"id": chat_id},
            "text": "/start",
        }
    }
    resp_guest = await telegram_bot.handle_update(db_session, update_guest)
    assert resp_guest["status"] == "processed"

    # 2. Start with valid signed link token
    link_token = generate_telegram_link_token(user.id, expires_in_minutes=15)
    update_link = {
        "message": {
            "chat": {"id": chat_id},
            "text": f"/start {link_token}",
        }
    }
    resp_link = await telegram_bot.handle_update(db_session, update_link)
    assert resp_link["status"] == "processed"

    # Verify user telegram_chat_id is now bound
    await db_session.refresh(user)
    assert user.telegram_chat_id == chat_id


@pytest.mark.asyncio
async def test_telegram_review_and_build_commands(db_session: AsyncSession, test_user):
    """Tests /review and /build commands in Telegram."""
    user, _ = test_user
    chat_id = "987654321"
    user.telegram_chat_id = chat_id
    await db_session.flush()

    # /review command
    update_review = {
        "message": {
            "chat": {"id": chat_id},
            "text": "/review Write some clean code etc to do stuff.",
        }
    }
    resp_review = await telegram_bot.handle_update(db_session, update_review)
    assert resp_review["status"] == "processed"
    assert resp_review["command"] == "/review"

    # /build command (creates project and begins discovery)
    update_build = {
        "message": {
            "chat": {"id": chat_id},
            "text": "/build Distributed Vector Search Service in Python",
        }
    }
    resp_build = await telegram_bot.handle_update(db_session, update_build)
    assert resp_build["status"] == "processed"
    assert resp_build["command"] == "/build"

    # /projects command
    update_proj = {
        "message": {
            "chat": {"id": chat_id},
            "text": "/projects",
        }
    }
    resp_proj = await telegram_bot.handle_update(db_session, update_proj)
    assert resp_proj["status"] == "processed"
    assert resp_proj["command"] == "/projects"


@pytest.mark.asyncio
async def test_telegram_duplicate_webhook_deduplication(db_session: AsyncSession, test_user):
    """Verifies that identical update_ids are rejected to prevent duplicate execution on network retries."""
    chat_id = "987654321"
    update_with_id = {
        "update_id": 99901,
        "message": {
            "chat": {"id": chat_id},
            "text": "/start",
        },
    }

    resp1 = await telegram_bot.handle_update(db_session, update_with_id)
    assert resp1["status"] == "processed"

    # Second delivery of same update_id
    resp2 = await telegram_bot.handle_update(db_session, update_with_id)
    assert resp2["status"] == "duplicate_ignored"
    assert resp2["update_id"] == 99901


@pytest.mark.asyncio
async def test_telegram_discovery_continuation(db_session: AsyncSession, test_user):
    """Verifies conversational discovery continuation over Telegram."""
    user, _ = test_user
    chat_id = "5551234"
    user.telegram_chat_id = chat_id
    await db_session.flush()

    # 1. Start build
    update_build = {
        "update_id": 99902,
        "message": {
            "chat": {"id": chat_id},
            "text": "/build Cloud Native Storage Engine",
        },
    }
    resp_build = await telegram_bot.handle_update(db_session, update_build)
    assert resp_build["status"] == "processed"
    assert resp_build["command"] == "/build"

    # 2. Conversational answer without slash command
    update_answer = {
        "update_id": 99903,
        "message": {
            "chat": {"id": chat_id},
            "text": "Targeting AWS S3 compatible storage with zero external dependencies.",
        },
    }
    resp_answer = await telegram_bot.handle_update(db_session, update_answer)
    assert resp_answer["status"] == "processed"
    assert resp_answer["command"] == "discovery_continuation"
