"""Telegram Webhook endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_db
from promptiq.telegram.bot import telegram_bot

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
async def telegram_webhook(update: dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Receives incoming updates from the official Telegram Bot API."""
    result = await telegram_bot.handle_update(db, update)
    return result
