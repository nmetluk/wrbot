"""
SQLAlchemy ORM models.

Все таблицы схемы из docs/architecture/data-model.md.
"""

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


class User(Base):
    """Таблица users — пользователи бота."""

    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notify_time: Mapped[time] = mapped_column(Time, nullable=False, default="10:00")
    tz: Mapped[str] = mapped_column(Text, nullable=False, default="Europe/Moscow")
    global_days: Mapped[str] = mapped_column(Text, nullable=False, default="[5,3,1]")  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Wallet(Base):
    """Таблица wallets — кошельки пользователей."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # FK→users.tg_id
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Category(Base):
    """Таблица categories — категории списаний."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # FK→users.tg_id
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Charge(Base):
    """Таблица charges — регулярные списания."""

    __tablename__ = "charges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # FK→users.tg_id
    name: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    wallet_id: Mapped[int] = mapped_column(Integer, nullable=False)  # FK→wallets.id
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # FK→categories.id
    next_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # once/monthly/quarterly/yearly
    individual_days: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON NULL
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active/done
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SentReminder(Base):
    """
    Таблица sent_reminders — отправленные напоминания.

    UNIQUE (charge_id, target_date, days_before) защищает от дублей.
    """

    __tablename__ = "sent_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charge_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # FK→charges.id
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    days_before: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("charge_id", "target_date", "days_before", name="uq_reminder"),
    )
