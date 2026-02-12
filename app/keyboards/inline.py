"""Inline-клавиатуры для навигации по журналу."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def journal_entry_buttons(entries: list[dict]) -> list[list[InlineKeyboardButton]]:
    """Кнопки для детального просмотра каждой записи."""
    rows = []
    for entry in entries:
        short = entry["short_message"][:40]
        rows.append([
            InlineKeyboardButton(
                text=f"f4c4 {entry['date']} — {short}",
                callback_data=f"journal:detail:{entry['analysis_id']}",
            )
        ])
    return rows


def journal_page_kb(entries: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Полная клавиатура страницы журнала: записи + навигация."""
    rows = journal_entry_buttons(entries)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"journal:page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="journal:noop")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"journal:page:{page + 1}")
        )
    rows.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def journal_detail_back_kb(page: int) -> InlineKeyboardMarkup:
    """Кнопка возврата к списку из детального просмотра."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку", callback_data=f"journal:page:{page}")]
    ])
