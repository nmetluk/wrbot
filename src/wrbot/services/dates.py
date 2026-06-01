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
