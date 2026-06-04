"""
Загрузчик справочника валют (bundled, оффлайн) — TASK-0049 / ADR-0013.

- currencies.json сгенерирован из ISO 4217 (153 активных валют).
- Модульный кэш: загружается один раз при импорте/первом вызове.
- API для TASK-0049 (отображение) и TASK-0050 (выбор: пресеты + поиск).
- format_amount: символ для пресетов (RUB/EUR/...), код для прочих.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from decimal import Decimal

# Ленивая загрузка + кэш (модульный)
_DATA: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _DATA
    if _DATA is None:
        data_path = Path(__file__).resolve().parent.parent / "data" / "currencies.json"
        _DATA = json.loads(data_path.read_text(encoding="utf-8"))
    return _DATA


def get_presets() -> list[str]:
    """Пресеты валют (RUB, EUR, USD, KZT, KGS) для кнопок выбора."""
    return cast("list[str]", list(_load()["presets"]))


def get_default() -> str:
    """Валюта по умолчанию (RUB)."""
    return cast("str", _load()["default"])


def get(code: str) -> dict[str, Any] | None:
    """Получить запись валюты по коду (code, name, minor, symbol?)."""
    data = _load()
    code_u = code.upper()
    for c in data["currencies"]:
        if c["code"] == code_u:
            return dict(c)  # копия
    return None


def is_valid_code(code: str) -> bool:
    """Валидный ли код валюты (из справочника)."""
    return get(code) is not None


def search(query: str) -> list[dict[str, Any]]:
    """
    Поиск валют по подстроке (code или name, case-insensitive).
    Для «Другая валюта» (TASK-0050): ввод кода/названия.
    """
    if not query or not query.strip():
        return []
    q = query.strip().upper()
    data = _load()
    results: list[dict[str, Any]] = []
    for c in data["currencies"]:
        if q in c["code"].upper() or q in c["name"].upper():
            results.append(dict(c))
    return results


def format_amount(amount: str | int | float | Decimal, code: str) -> str:
    """
    Форматировать сумму с валютой: "{amount} {symbol|code}".
    - Для пресетов: символ если есть (₽, €, $, ...).
    - Для прочих: код (USD, AED, ...).
    Оффлайн. Анти-дрейф: реальный вызов в тестах форматтеров.
    """
    cur = get(code) or {}
    presets = get_presets()
    suffix = cur["symbol"] if code in presets and "symbol" in cur else code
    amt_str = str(amount)
    return f"{amt_str} {suffix}"


def get_all() -> list[dict[str, Any]]:
    """Полный список активных валют (для пагинации 'Другая валюта')."""
    return [dict(c) for c in _load()["currencies"]]


def get_page(page: int = 0, per_page: int = 8) -> tuple[list[dict[str, Any]], int]:
    """
    Постраничный доступ к списку валют (для инлайн-списка с пагинацией).
    Возвращает (items, total_pages). page 0-based, clamped.
    per_page ~8-10 чтобы влезло в клавиатуру.
    """
    all_c = get_all()
    total = len(all_c)
    if total == 0:
        return [], 0
    total_pages = (total + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    return all_c[start:end], total_pages
