"""Обработчик текстовых сообщений — анализ через LLM и сохранение в БД."""

import logging

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repositories.user import UserRepository
from app.database.repositories.analysis import AnalysisRepository
from app.services.analysis import AnalysisService
from app.services.pattern_tracker import detect_patterns, patterns_to_json
from app.utils.text_formatter import split_message
from app.utils.typing_action import typing_action

logger = logging.getLogger(__name__)

analyze_router = Router(name="analyze")
analysis_service = AnalysisService()


@analyze_router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, session: AsyncSession) -> None:
    """Анализирует текст пользователя и сохраняет результат в БД."""
    # Получить или создать пользователя
    user = await UserRepository.get_or_create(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
    )

    async with typing_action(message.bot, message.chat.id):
        try:
            response = await analysis_service.analyze(message.text)
        except Exception:
            logger.exception("Analysis failed for user %s", message.from_user.id)
            await message.answer(
                "Произошла ошибка при анализе. Попробуйте позже."
            )
            return

    # Определить паттерны в ответе LLM
    detected = detect_patterns(response.content)
    patterns_json = patterns_to_json(detected)

    # Сохранить анализ в БД
    try:
        await AnalysisRepository.create(
            session,
            user_id=user.id,
            user_message=message.text,
            bot_response=response.content,
            llm_provider=settings.llm_provider,
            llm_model=response.model,
            tokens_used=response.tokens_used,
            detected_patterns=patterns_json,
        )
        await UserRepository.increment_analysis_count(session, message.from_user.id)
        await UserRepository.update_last_active(session, message.from_user.id)
    except Exception:
        logger.exception("Failed to save analysis to DB for user %s", message.from_user.id)

    parts = split_message(response.content)
    for part in parts:
        await message.answer(part)
