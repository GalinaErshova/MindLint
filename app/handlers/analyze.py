"""Обработчик текстовых сообщений — анализ через LLM, FSM для уточнений."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repositories.analysis import AnalysisRepository
from app.database.repositories.user import UserRepository
from app.keyboards.inline import analysis_actions_kb
from app.services.analysis import AnalysisService
from app.services.pattern_tracker import detect_patterns, patterns_to_json
from app.states.analysis import AnalysisStates
from app.utils.text_formatter import split_message
from app.utils.typing_action import typing_action

logger = logging.getLogger(__name__)

analyze_router = Router(name="analyze")
analysis_service = AnalysisService()


@analyze_router.message(AnalysisStates.waiting_for_clarification, F.text)
async def handle_clarification(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    """Обработка уточняющего ответа пользователя в FSM-режиме."""
    data = await state.get_data()
    history: list[dict[str, str]] = data.get("history", [])

    user = await UserRepository.get_or_create(
        session, telegram_id=message.from_user.id
    )

    async with typing_action(message.bot, message.chat.id):
        try:
            response = await analysis_service.continue_analysis(
                conversation_history=history,
                new_message=message.text,
            )
        except Exception:
            logger.exception("Clarification failed for user %s", message.from_user.id)
            await message.answer("Произошла ошибка при анализе. Попробуйте позже.")
            await state.clear()
            return

    # Обновить историю
    history.append({"role": "user", "content": message.text})
    history.append({"role": "assistant", "content": response.content})
    await state.update_data(history=history)

    # Определить паттерны и сохранить
    detected = detect_patterns(response.content)
    patterns_json = patterns_to_json(detected)

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
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            await message.answer(part, reply_markup=analysis_actions_kb())
        else:
            await message.answer(part)


@analyze_router.callback_query(F.data == "analysis:clarify")
async def cb_clarify(callback: CallbackQuery, state: FSMContext) -> None:
    """Нажата кнопка 'Уточнить' — перевести в режим ожидания уточнения."""
    await state.set_state(AnalysisStates.waiting_for_clarification)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Напишите уточнение или ответ на вопрос. Я продолжу анализ с учётом контекста."
    )
    await callback.answer()


@analyze_router.callback_query(F.data == "analysis:finish")
async def cb_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Нажата кнопка 'Завершить' — очистить FSM."""
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Анализ завершён.")


@analyze_router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Первичный анализ текста пользователя."""
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
            await message.answer("Произошла ошибка при анализе. Попробуйте позже.")
            return

    # Сохранить историю в FSM для возможного продолжения
    history = [
        {"role": "user", "content": message.text},
        {"role": "assistant", "content": response.content},
    ]
    await state.update_data(history=history)

    # Определить паттерны и сохранить в БД
    detected = detect_patterns(response.content)
    patterns_json = patterns_to_json(detected)

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

    # Отправить ответ с кнопками
    parts = split_message(response.content)
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            await message.answer(part, reply_markup=analysis_actions_kb())
        else:
            await message.answer(part)
