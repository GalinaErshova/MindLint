def escape_markdown_v2(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for char in text:
        if char in special_chars:
            escaped += f"\\{char}"
        else:
            escaped += char
    return escaped


def split_message(text: str, max_len: int = 4096) -> list[str]:
    if len(text) <= max_len:
        return [text]

    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break

        # Ищем последний перенос строки в пределах лимита
        split_pos = text.rfind("\n", 0, max_len)
        if split_pos == -1:
            # Нет переноса — ищем пробел
            split_pos = text.rfind(" ", 0, max_len)
        if split_pos == -1:
            # Нет пробела — режем по лимиту
            split_pos = max_len

        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return parts
