"""Обработчики команды /journal — просмотр истории анализов."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import journal_detail_back_kb, journal_page_kb
from app.services.journal import JournalService
from app.utils.text_formatter import split_message

logger = logging.getLogger(__name__)

journal_router = Router(name="journal")


@journal_router.message(Command("journal"))
async def cmd_journal(message: Message, session: AsyncSession) -> None:
    """Команда /journal — показать первую страницу журнала."""
    await _show_journal_page(message, session, page=1)


@journal_router.callback_query(F.data.startswith("journal:page:"))
async def cb_journal_page(callback: CallbackQuery, session: AsyncSession) -> None:
    """Навигация по страницам журнала."""
    page = int(callback.data.split(":")[2])
    await _edit_journal_page(callback, session, page)


@journal_router.callback_query(F.data == "journal:noop")
async def cb_journal_noop(callback: CallbackQuery) -> None:
    """Игнорировать нажатие на индикатор страницы."""
    await callback.answer()


@journal_router.callback_query(F.data.startswith("journal:detail:"))
async def cb_journal_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    """Детальный просмотр записи журнала."""
    analysis_id = int(callback.data.split(":")[2])

    analysis = await JournalService.get_analysis_detail(session, analysis_id)
    if not analysis:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    telegram_id = callback.from_user.id
    total_pages = await JournalService.get_total_pages(session, telegram_id)

    date_str = analysis.created_at.strftime("%d.%m.%Y %H:%M")
    text = (
        f"<b>Запись от {date_str}</b>\n\n"
        f"<b>Ваш запрос:</b>\n{analysis.user_message}\n\n"
        f"<b>Анализ:</b>\n{analysis.bot_response}"
    )

    parts = split_message(text)
    try:
        await callback.message.edit_text(
            parts[0],
            reply_markup=journal_detail_back_kb(page=1),
        )
    except Exception:
        await callback.message.answer(
            parts[0], reply_markup=journal_detail_back_kb(page=1)
        )

    for part in parts[1:]:
        await callback.message.answer(part)

    await callback.answer()


async def _show_journal_page(
    message: Message, session: AsyncSession, page: int
) -> None:
    """Отправить страницу журнала как новое сообщение."""
    telegram_id = message.from_user.id
    total_pages = await JournalService.get_total_pages(session, telegram_id)
    entries = await JournalService.get_user_journal(session, telegram_id, page)

    if not entries:
        await message.answer(
            "Вы ещё не отправляли запросов. Напишите что-нибудь для анализа!"
        )
        return

    text = _format_journal_page(entries, page, total_pages)
    kb = journal_page_kb(entries, page, total_pages)
    await message.answer(text, reply_markup=kb)


async def _edit_journal_page(
    callback: CallbackQuery, session: AsyncSession, page: int
) -> None:
    """Обновить сообщение с новой страницей журнала."""
    telegram_id = callback.from_user.id
    total_pages = await JournalService.get_total_pages(session, telegram_id)

    page = max(1, min(page, total_pages))

    entries = await JournalService.get_user_journal(session, telegram_id, page)
    text = _format_journal_page(entries, page, total_pages)
    kb = journal_page_kb(entries, page, total_pages)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass

    await callback.answer()


def _format_journal_page(entries: list[dict], page: int, total_pages: int) -> str:
    """Форматировать страницу журнала в текст."""
    lines = [f"<b>Журнал анализов</b> (стр. {page}/{total_pages})\n"]

    for i, entry in enumerate(entries, start=1):
        lines.append(
            f"{i}. <b>{entry['date']}</b>\n"
            f"   {entry['short_message']}\n"
            f"   <i>{entry['short_response']}</i>\n"
        )

    lines.append("Нажмите на запись для полного просмотра.")
    return "\n".join(lines)
