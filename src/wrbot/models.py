"""
Domain models and types.

Место для pydantic моделей или dataclass, представляющих доменные сущности.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

# Перечисления для статусов и периодов
ChargeStatus = Literal["active", "done"]
ChargePeriod = Literal["once", "monthly", "quarterly", "yearly"]


@dataclass(frozen=True)
class User:
    """Доменная модель пользователя."""

    tg_id: int
    notify_time: time
    tz: str
    global_days: list[int]
    created_at: datetime


@dataclass(frozen=True)
class Wallet:
    """Доменная модель кошелька."""

    id: int
    user_id: int
    name: str


@dataclass(frozen=True)
class Category:
    """Доменная модель категории."""

    id: int
    user_id: int
    name: str


@dataclass(frozen=True)
class Charge:
    """Доменная модель списания."""

    id: int
    user_id: int
    name: str
    amount: Decimal
    wallet_id: int
    category_id: int | None
    next_date: date
    period: ChargePeriod
    individual_days: list[int] | None
    status: ChargeStatus
    paid_at: datetime | None
    snoozed_until: date | None
    created_at: datetime


@dataclass(frozen=True)
class SentReminder:
    """Доменная модель отправленного напоминания."""

    id: int
    charge_id: int
    target_date: date
    days_before: int
    sent_at: datetime


@dataclass(frozen=True)
class ReminderJob:
    """Модель задачи планировщика для напоминания."""

    charge_id: int
    user_id: int
    charge_name: str
    amount: Decimal
    target_date: date
    days_before: int
    notify_time: time
    tz: str
