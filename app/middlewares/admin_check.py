"""Middleware для логирования попыток доступа к админ-командам."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.config import settings

logger = logging.getLogger(__name__)

ADMIN_COMMANDS = {"/stats", "/broadcast"}


class AdminCheckMiddleware(BaseMiddleware):
    """Логирует попытки обычных пользователей вызвать админ-команды."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lower() if event.text.startswith("/") else None
            if command in ADMIN_COMMANDS and event.from_user:
                if event.from_user.id not in settings.admin_ids:
                    logger.warning(
                        "Non-admin access attempt: user=%d, command=%s",
                        event.from_user.id,
                        command,
                    )

        return await handler(event, data)
