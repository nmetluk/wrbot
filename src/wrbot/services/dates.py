"""
Date and period calculation utilities.

Функции для расчёта следующей даты списания с учётом периода.
"""

from calendar import monthrange
from datetime import date

from wrbot.models import ChargePeriod


def _add_months(d: date, months: int) -> date:
    """Add months with clamp to last day of target month (per ADR-0006)."""
    if months <= 0:
        return d
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_next_date(current: date, period: ChargePeriod) -> date:
    """
    Рассчитать следующую дату списания.

    Args:
        current: Текущая дата next_date
        period: Период списания

    Returns:
        Следующая дата с учётом clamp к последнему дню месяца (ADR-0006)
    """
    if period == "once":
        # Для одноразовых сдвиг не применяется (обрабатывается как done в mark_paid)
        return current
    if period == "monthly":
        return _add_months(current, 1)
    if period == "quarterly":
        return _add_months(current, 3)
    if period == "yearly":
        return _add_months(current, 12)
    # Fallback (не должен случаться при валидации)
    return current


def get_period_upper_bound(today: date, period: ChargePeriod) -> date | None:
    """
    Верхняя граница (включительно) для next_date при данном периоде.

    Для 'once' — None (без верхней границы).
    Использует _add_months с clamp конца месяца (ADR-0006).
    """
    if period == "once":
        return None
    months_map: dict[ChargePeriod, int] = {"monthly": 1, "quarterly": 3, "yearly": 12}
    months = months_map[period]
    return _add_months(today, months)


def validate_next_date(period: ChargePeriod, d: date, today: date | None = None) -> None:
    """
    Чистая функция валидации даты следующего списания (TASK-0040).

    Правила (по решению владельца):
    - d > today
    - для once: без верхней границы
    - для monthly/quarterly/yearly: d <= today + период (с clamp конца месяца по ADR-0006)

    Raises:
        ValueError: с сообщением (UI-слой форматирует под локаль и показывает окно).
    """
    if today is None:
        today = date.today()
    if d <= today:
        raise ValueError("Дата должна быть строго после сегодня.")
    upper = get_period_upper_bound(today, period)
    if upper is not None and d > upper:
        raise ValueError(f"Дата для периода {period} не должна быть позже {upper}.")
