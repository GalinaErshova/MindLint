"""Репозиторий для работы с пользователями."""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


class UserRepository:

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        telegram_id: int,
        **kwargs,
    ) -> User:
        """Получить пользователя по telegram_id или создать нового."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(telegram_id=telegram_id, **kwargs)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user

    @staticmethod
    async def update_last_active(session: AsyncSession, telegram_id: int) -> None:
        """Обновить время последней активности пользователя."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.last_active_at = datetime.utcnow()
            await session.commit()

    @staticmethod
    async def increment_analysis_count(session: AsyncSession, telegram_id: int) -> None:
        """Увеличить счётчик анализов пользователя на 1."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.analysis_count = user.analysis_count + 1
            await session.commit()

    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        """Общая статистика: кол-во пользователей, активных, всего анализов."""
        total = await session.scalar(select(func.count(User.id)))
        active = await session.scalar(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )
        total_analyses = await session.scalar(select(func.sum(User.analysis_count)))

        return {
            "total_users": total or 0,
            "active_users": active or 0,
            "total_analyses": total_analyses or 0,
        }
