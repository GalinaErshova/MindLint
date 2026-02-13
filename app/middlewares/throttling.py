"""Rate limiting middleware — ограничение частоты сообщений."""

import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)

# Лимит: максимум сообщений за период
MAX_MESSAGES = 5
PERIOD_SECONDS = 60


class ThrottlingMiddleware(BaseMiddleware):
    """Ограничивает количество сообщений от пользователя: MAX_MESSAGES за PERIOD_SECONDS."""

    def __init__(self) -> None:
        self._user_timestamps: dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = time.time()
        timestamps = self._user_timestamps.get(user_id, [])

        # Убрать устаревшие записи
        timestamps = [t for t in timestamps if now - t < PERIOD_SECONDS]

        if len(timestamps) >= MAX_MESSAGES:
            logger.warning("Throttled user %d: %d messages in %ds", user_id, len(timestamps), PERIOD_SECONDS)
            await event.answer(
                "Подождите немного перед следующим запросом."
            )
            self._user_timestamps[user_id] = timestamps
            return None

        timestamps.append(now)
        self._user_timestamps[user_id] = timestamps

        return await handler(event, data)
