"""Inline-клавиатуры: журнал, анализ."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# --- Кнопки анализа (FSM) ---

def analysis_actions_kb() -> InlineKeyboardMarkup:
    """Кнопки после анализа: Уточнить / Завершить."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="\U0001f50d Уточнить",
                callback_data="analysis:clarify",
            ),
            InlineKeyboardButton(
                text="\u2705 Завершить",
                callback_data="analysis:finish",
            ),
        ]
    ])


# --- Кнопки журнала ---


def journal_entry_buttons(entries: list[dict]) -> list[list[InlineKeyboardButton]]:
    """Кнопки для детального просмотра каждой записи."""
    rows = []
    for entry in entries:
        short = entry["short_message"][:40]
        rows.append([
            InlineKeyboardButton(
                text=f"\U0001f4c4 {entry['date']} \u2014 {short}",
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
            InlineKeyboardButton(text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data=f"journal:page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="journal:noop")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="\u0412\u043f\u0435\u0440\u0451\u0434 \u27a1\ufe0f", callback_data=f"journal:page:{page + 1}")
        )
    rows.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def journal_detail_back_kb(page: int) -> InlineKeyboardMarkup:
    """Кнопка возврата к списку из детального просмотра."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f \u041a \u0441\u043f\u0438\u0441\u043a\u0443", callback_data=f"journal:page:{page}")]
    ])
