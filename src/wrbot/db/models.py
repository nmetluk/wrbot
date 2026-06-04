"""
SQLAlchemy ORM models.

Все таблицы схемы из docs/architecture/data-model.md.
Связи через ForeignKey с ON DELETE CASCADE где уместно.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


class User(Base):
    """Таблица users — пользователи бота."""

    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notify_time: Mapped[time] = mapped_column(Time, nullable=False, default=lambda: time(10, 0))
    tz: Mapped[str] = mapped_column(Text, nullable=False, default="Europe/Moscow")
    global_days: Mapped[str] = mapped_column(Text, nullable=False, default="[5,3,1]")  # JSON
    last_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )

    # Relationships
    wallets: Mapped[list["Wallet"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    charges: Mapped[list["Charge"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Wallet(Base):
    """Таблица wallets — кошельки пользователей."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False, default="👛")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="wallets")
    charges: Mapped[list["Charge"]] = relationship(back_populates="wallet")


class Category(Base):
    """Таблица categories — категории списаний."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # notify_chat_ids: JSON list[int] chat_id для дубля (TASK-0043/ADR-0012)
    notify_chat_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="categories")
    charges: Mapped[list["Charge"]] = relationship(back_populates="category")


class Charge(Base):
    """Таблица charges — регулярные списания."""

    __tablename__ = "charges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    next_date: Mapped[date] = mapped_column(Date, nullable=False)  # Date вместо DateTime
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # once/monthly/quarterly/yearly
    individual_days: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON NULL
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active/done
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    snoozed_until: Mapped[date | None] = mapped_column(Date, nullable=True)  # Date вместо DateTime
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="charges")
    wallet: Mapped["Wallet"] = relationship(back_populates="charges")
    category: Mapped[Optional["Category"]] = relationship(back_populates="charges")
    sent_reminders: Mapped[list["SentReminder"]] = relationship(
        back_populates="charge", cascade="all, delete-orphan"
    )


class SentReminder(Base):
    """
    Таблица sent_reminders — отправленные напоминания.

    UNIQUE (charge_id, target_date, days_before) защищает от дублей.
    ON DELETE CASCADE для charge_id.
    """

    __tablename__ = "sent_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charge_id: Mapped[int] = mapped_column(
        ForeignKey("charges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)  # Date вместо DateTime
    days_before: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("charge_id", "target_date", "days_before", name="uq_reminder"),
    )

    # Relationships
    charge: Mapped["Charge"] = relationship(back_populates="sent_reminders")


class AuditLog(Base):
    """
    Таблица audit_log — аудит действий (M6, TASK-0032, ADR-0010).

    Без чувствительных данных (сумм, имён, текстов).
    actor_id без FK (чтобы не терять при удалении user).
    actor_role: user/admin/system.
    action: строковый тип (e.g. 'charge.create', 'wallet.delete').
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/admin/system
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. charge.create
    entity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # charge/wallet/...
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )

    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_actor_id_created_at", "actor_id", "created_at"),
    )
