"""
Date and period calculation utilities.

Функции для расчёта следующей даты списания с учётом периода.
"""

from datetime import date

from wrbot.models import ChargePeriod


def calculate_next_date(current: date, period: ChargePeriod) -> date:
    """
    Рассчитать следующую дату списания.

    Args:
        current: Текущая дата next_date
        period: Период списания

    Returns:
        Следующая дата с учётом clamp к последнему дню месяца
    """
    # TODO: M2 - реализовать логику сдвига даты
    # - monthly: +1 месяц с clamp
    # - quarterly: +3 месяца
    # - yearly: +12 месяцев
    # - once: не используется (одноразовые становятся done)
    return current
