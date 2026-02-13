"""Обработчик команды /patterns — сводка паттернов мышления."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pattern_tracker import PatternTracker

logger = logging.getLogger(__name__)

patterns_router = Router(name="patterns")


@patterns_router.message(Command("patterns"))
async def cmd_patterns(message: Message, session: AsyncSession) -> None:
    """Показать сводку паттернов пользователя."""
    data = await PatternTracker.get_user_patterns(session, message.from_user.id)
    text = PatternTracker.format_patterns_text(data)
    await message.answer(text)
