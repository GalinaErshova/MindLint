from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.handlers.start import start_router
from app.handlers.analyze import analyze_router


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    register_routers(dp)
    return dp


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(analyze_router)  # последним — catch-all для текста
