"""
Валидаторы пользовательского ввода (TASK-0043 и т.п.).
"""

from __future__ import annotations


def is_valid_chat_id(value: str | int | None) -> bool:
    """
    Валидация chat_id для notify targets (TASK-0043 / ADR-0012).

    - Только числовой (int).
    - Каналы/супергруппы обычно отрицательные (-1001234567890).
    - В v1 @username не поддерживаем (сообщить пользователю).
    - Минимум разумный диапазон (не 0, не слишком короткий).
    """
    if value is None:
        return False
    s = str(value) if isinstance(value, int) else str(value).strip()
    if not s or s == "-" or s == "0":
        return False
    # @username в v1 не поддерживаем
    if s.startswith("@"):
        return False
    try:
        cid = int(s)
    except ValueError:
        return False
    # разумный диапазон
    return not (abs(cid) < 10 or abs(cid) > 10**14)


def parse_chat_id(value: str | int | None) -> int | None:
    """Вернуть int chat_id если валиден, иначе None."""
    if value is None:
        return None
    s = str(value) if isinstance(value, int) else str(value).strip()
    if not is_valid_chat_id(s):
        return None
    try:
        return int(s)
    except ValueError:
        return None
