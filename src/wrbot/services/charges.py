"""
Сервисы для работы со списаниями (M3).

Валидация сумм, периодов, лимитов.
"""

from decimal import Decimal

from wrbot.models import ChargePeriod
from wrbot.services.reference import (
    InvalidAmount,
    validate_amount,
)


def validate_period(raw: str) -> ChargePeriod:
    """
    Валидировать период списания.

    Args:
        raw: Строка периода от пользователя

    Returns:
        Валидный ChargePeriod

    Raises:
        InvalidAmount: переиспользуем для простоты, или можно сделать отдельный
    """
    allowed: set[ChargePeriod] = {"once", "monthly", "quarterly", "yearly"}
    if raw not in allowed:
        raise InvalidAmount(
            f"Недопустимый период: {raw}. Допустимы: once, monthly, quarterly, yearly"
        )
    return raw


def validate_charge_amount(raw: str | Decimal | float | int) -> Decimal:
    """Обёртка над validate_amount для явности в контексте списаний."""
    return validate_amount(raw)
