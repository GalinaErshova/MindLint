"""Репозиторий для работы с анализами."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.analysis import Analysis


class AnalysisRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        user_message: str,
        bot_response: str,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        tokens_used: int = 0,
        detected_patterns: str | None = None,
    ) -> Analysis:
        """Сохранить результат анализа в БД."""
        analysis = Analysis(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            llm_provider=llm_provider,
            llm_model=llm_model,
            tokens_used=tokens_used,
            detected_patterns=detected_patterns,
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)
        return analysis

    @staticmethod
    async def get_by_user(
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Analysis]:
        """Получить анализы пользователя с пагинацией."""
        stmt = (
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, analysis_id: int) -> Analysis | None:
        """Получить анализ по ID."""
        stmt = select(Analysis).where(Analysis.id == analysis_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def count_by_user(session: AsyncSession, user_id: int) -> int:
        """Подсчитать количество анализов пользователя."""
        stmt = select(func.count(Analysis.id)).where(Analysis.user_id == user_id)
        result = await session.scalar(stmt)
        return result or 0
