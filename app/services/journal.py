"""Сервис журнала решений — выборка анализов с пагинацией."""

import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.analysis import AnalysisRepository
from app.database.repositories.user import UserRepository


class JournalService:

    PER_PAGE = 5

    @staticmethod
    async def get_user_journal(
        session: AsyncSession,
        telegram_id: int,
        page: int = 1,
        per_page: int = 5,
    ) -> list[dict]:
        """Получить страницу журнала пользователя.

        Возвращает список записей с краткими текстами:
        - date: дата анализа
        - short_message: первые 100 символов запроса
        - short_response: первые 200 символов ответа
        - analysis_id: ID для детального просмотра
        """
        user = await UserRepository.get_or_create(session, telegram_id)
        offset = (page - 1) * per_page

        analyses = await AnalysisRepository.get_by_user(
            session, user_id=user.id, limit=per_page, offset=offset
        )

        entries = []
        for a in analyses:
            entries.append({
                "analysis_id": a.id,
                "date": a.created_at.strftime("%d.%m.%Y %H:%M"),
                "short_message": _truncate(a.user_message, 100),
                "short_response": _truncate(a.bot_response, 200),
            })
        return entries

    @staticmethod
    async def get_total_pages(
        session: AsyncSession,
        telegram_id: int,
        per_page: int = 5,
    ) -> int:
        """Подсчитать общее количество страниц журнала."""
        user = await UserRepository.get_or_create(session, telegram_id)
        total = await AnalysisRepository.count_by_user(session, user.id)
        return max(1, math.ceil(total / per_page))

    @staticmethod
    async def get_analysis_detail(
        session: AsyncSession,
        analysis_id: int,
    ):
        """Получить полный анализ по ID."""
        return await AnalysisRepository.get_by_id(session, analysis_id)


def _truncate(text: str, max_len: int) -> str:
    """Обрезать текст до max_len символов с многоточием."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"
