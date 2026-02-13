"""Сервис отслеживания паттернов логических ошибок."""

import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.analysis import AnalysisRepository
from app.database.repositories.user import UserRepository

logger = logging.getLogger(__name__)

# 5 паттернов из системного промпта MindLint
PATTERNS = {
    "A": {
        "name": "Подмена причины ощущением",
        "markers": [
            r"паттерн\s*a",
            r"подмена\s+причины",
            r"не\s+могу.*без\s+метрик",
            r"ощущение\s+вместо\s+причины",
            r"причин[аыу]\s+ощущени",
        ],
    },
    "B": {
        "name": "Ложная необходимость",
        "markers": [
            r"паттерн\s*b",
            r"ложн\w+\s+необходимост",
            r"нужно\s+сначала",
            r"обязательно\s+ли.*для",
            r"необходим\w+\s+условие\s+не\s+подтвержден",
        ],
    },
    "C": {
        "name": "Циклическая логика",
        "markers": [
            r"паттерн\s*c",
            r"цикличес\w+\s+логик",
            r"замкнут\w+\s+(круг|цикл)",
            r"причина\s+и\s+следствие\s+взаимно",
            r"выход\w*\s+из\s+цикл",
        ],
    },
    "D": {
        "name": "Неопределённое условие",
        "markers": [
            r"паттерн\s*d",
            r"неопределённ\w+\s+услови",
            r"неопределенн\w+\s+услови",
            r"когда\s+буд\w+\s+(готов|подходящ|время)",
            r"признак\w*\s+выполнен",
            r"условие\s+не\s+определен",
        ],
    },
    "E": {
        "name": "Универсальное оправдание",
        "markers": [
            r"паттерн\s*e",
            r"универсальн\w+\s+оправдани",
            r"одна\s+причина\s+объясня\w+\s+всё",
            r"одна\s+причина\s+объясня\w+\s+все",
            r"единственн\w+\s+(причин|объяснени)",
        ],
    },
}


def detect_patterns(bot_response: str) -> list[str]:
    """Определить паттерны, упомянутые в ответе LLM.

    Возвращает список кодов паттернов (например, ["A", "D"]).
    """
    text_lower = bot_response.lower()
    found = []

    for code, info in PATTERNS.items():
        for marker in info["markers"]:
            if re.search(marker, text_lower):
                found.append(code)
                break

    return found


def patterns_to_json(patterns: list[str]) -> str | None:
    """Сериализовать список паттернов в JSON для хранения в БД."""
    if not patterns:
        return None
    return json.dumps(patterns)


def patterns_from_json(json_str: str | None) -> list[str]:
    """Десериализовать список паттернов из JSON."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return []


class PatternTracker:

    @staticmethod
    async def get_user_patterns(
        session: AsyncSession,
        telegram_id: int,
    ) -> dict:
        """Получить сводку паттернов пользователя.

        Возвращает:
        {
            "total_analyses": int,
            "patterns": {
                "A": {"name": "...", "count": N},
                "B": {"name": "...", "count": N},
                ...
            }
        }
        """
        user = await UserRepository.get_or_create(session, telegram_id)

        # Загрузить все анализы пользователя
        total = await AnalysisRepository.count_by_user(session, user.id)
        analyses = await AnalysisRepository.get_by_user(
            session, user_id=user.id, limit=total, offset=0
        )

        # Подсчитать паттерны
        counts: dict[str, int] = {code: 0 for code in PATTERNS}

        for analysis in analyses:
            # Сначала проверить сохранённые паттерны
            stored = patterns_from_json(analysis.detected_patterns)
            if stored:
                for code in stored:
                    if code in counts:
                        counts[code] += 1
            else:
                # Fallback: парсить ответ заново
                detected = detect_patterns(analysis.bot_response)
                for code in detected:
                    counts[code] += 1

        result = {
            "total_analyses": total,
            "patterns": {},
        }
        for code, info in PATTERNS.items():
            result["patterns"][code] = {
                "name": info["name"],
                "count": counts[code],
            }

        return result

    @staticmethod
    def format_patterns_text(data: dict) -> str:
        """Форматировать сводку паттернов для отправки пользователю."""
        total = data["total_analyses"]

        if total < 3:
            return (
                "Нужно больше анализов для выявления паттернов.\n"
                f"Сейчас: {total} из 3 необходимых.\n\n"
                "Отправьте ещё несколько утверждений для анализа."
            )

        lines = [f"<b>Ваши паттерны за {total} анализов:</b>\n"]

        # Сортировать по частоте (от большего к меньшему)
        sorted_patterns = sorted(
            data["patterns"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )

        max_count = max(p["count"] for p in data["patterns"].values()) or 1

        for code, info in sorted_patterns:
            count = info["count"]
            name = info["name"]
            bar = _progress_bar(count, max_count)
            lines.append(f"{bar} <b>{name}</b> \u2014 {count} раз")

        # Добавить пояснение по самому частому паттерну
        top_code, top_info = sorted_patterns[0]
        if top_info["count"] > 0:
            lines.append(
                f"\nЧаще всего встречается: <b>{top_info['name']}</b> "
                f"(паттерн {top_code})"
            )
        else:
            lines.append("\nПаттернов пока не обнаружено. Логика в порядке!")

        return "\n".join(lines)


def _progress_bar(value: int, max_value: int, width: int = 5) -> str:
    """Текстовый прогресс-бар: \u2588\u2588\u2588\u2591\u2591."""
    if max_value == 0:
        filled = 0
    else:
        filled = round(value / max_value * width)
    return "\u2588" * filled + "\u2591" * (width - filled)
