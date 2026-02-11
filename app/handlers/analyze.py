import logging

from aiogram import F, Router
from aiogram.types import Message

from app.services.analysis import AnalysisService
from app.utils.text_formatter import split_message
from app.utils.typing_action import typing_action

logger = logging.getLogger(__name__)

analyze_router = Router(name="analyze")
analysis_service = AnalysisService()


@analyze_router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    async with typing_action(message.bot, message.chat.id):
        try:
            response = await analysis_service.analyze(message.text)
        except Exception:
            await message.answer(
                "Произошла ошибка при анализе. Попробуйте позже."
            )
            return

    parts = split_message(response.content)
    for part in parts:
        await message.answer(part)
