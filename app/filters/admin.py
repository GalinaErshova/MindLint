"""Фильтр проверки прав администратора."""

from aiogram.filters import Filter
from aiogram.types import Message

from app.config import settings


class IsAdmin(Filter):
    """Пропускает только пользователей из списка ADMIN_IDS."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.admin_ids
