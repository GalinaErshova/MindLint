"""Админ-команды: /stats, /broadcast."""

import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user import UserRepository
from app.filters.admin import IsAdmin

logger = logging.getLogger(__name__)

admin_router = Router(name="admin")
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    """Статистика бота — только для админов."""
    stats = await UserRepository.get_stats(session)

    text = (
        "<b>Статистика MindLint</b>\n\n"
        f"Пользователей всего: {stats['total_users']}\n"
        f"Активных: {stats['active_users']}\n"
        f"Активных за сегодня: {stats['active_today']}\n\n"
        f"Анализов всего: {stats['total_analyses']}\n"
        f"Анализов за сегодня: {stats['analyses_today']}"
    )
    await message.answer(text)


@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Рассылка сообщения всем активным пользователям."""
    # Извлечь текст после команды
    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    users = await UserRepository.get_active_users(session)
    sent = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(chat_id=user.telegram_id, text=text)
            sent += 1
        except Exception:
            logger.warning("Failed to send broadcast to user %d", user.telegram_id)
            failed += 1

    await message.answer(
        f"Рассылка завершена.\n"
        f"Отправлено: {sent}\n"
        f"Не доставлено: {failed}"
    )
