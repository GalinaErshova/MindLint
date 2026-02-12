"""Middleware для инъекции AsyncSession в каждый запрос."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.engine import async_session

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Создаёт AsyncSession для каждого запроса и передаёт через data["session"]."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            return result
