from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "<b>Привет! Я MindLint</b> — бот-психолог с ИИ.\n\n"
        "Я помогу тебе разобраться в мыслях, найти когнитивные искажения "
        "и посмотреть на ситуацию под другим углом.\n\n"
        "Просто напиши мне свою мысль или ситуацию, "
        "и я проведу мягкий анализ.\n\n"
        "Используй /help, чтобы узнать все команды."
    )


@start_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Доступные команды:</b>\n\n"
        "/start — начать работу с ботом\n"
        "/journal — журнал анализов\n"
        "/help — справка по командам\n"
    )
