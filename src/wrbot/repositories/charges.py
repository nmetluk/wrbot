"""
Charge repository.

Доступ к данным списаний с изоляцией по user_id (FR-13).
Включает логику mark_paid (сдвиг периода или мягкое закрытие).
"""

import logging
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import Charge
from wrbot.models import ChargePeriod
from wrbot.repositories.audit_log import (
    ACTION_CHARGE_CREATE,
    ACTION_CHARGE_DELETE,
    ACTION_CHARGE_EDIT,
    ACTION_CHARGE_PAID,
    ACTION_CHARGE_SNOOZE,
    AuditLogRepository,
)
from wrbot.services.charges import validate_charge_amount, validate_period
from wrbot.services.dates import calculate_next_date
from wrbot.services.reference import (
    check_charge_limit,
)

logger = logging.getLogger(__name__)


class ChargeRepository:
    """Репозиторий для работы со списаниями."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        name: str,
        amount: Decimal,
        wallet_id: int,
        category_id: int | None,
        next_date: date,
        period: ChargePeriod,
    ) -> Charge:
        """
        Создать новое списание для пользователя.

        Args:
            user_id: ID пользователя (tg_id)
            name: Название списания
            amount: Сумма (Decimal)
            wallet_id: ID кошелька
            category_id: ID категории (опционально)
            next_date: Дата следующего списания
            period: Период (once/monthly/quarterly/yearly)

        Returns:
            Созданное списание

        Raises:
            InvalidAmount: если сумма некорректна
            LimitExceeded: если превышен лимит активных списаний
        """
        validated_amount = validate_charge_amount(amount)
        validated_period = validate_period(period)

        # Проверка лимита активных списаний
        result = await self._session.execute(
            select(Charge.id).where(Charge.user_id == user_id, Charge.status == "active")
        )
        count = len(result.all())
        check_charge_limit(count)

        charge = Charge(
            user_id=user_id,
            name=name.strip(),
            amount=validated_amount,
            wallet_id=wallet_id,
            category_id=category_id,
            next_date=next_date,
            period=validated_period,
            status="active",
        )
        self._session.add(charge)
        await self._session.flush()
        logger.info(
            "Created charge: user_id=%s, name=%s, amount=%s, period=%s",
            user_id,
            name,
            validated_amount,
            validated_period,
        )
        # Audit (TASK-0032)
        await AuditLogRepository(self._session).record(
            actor_id=user_id,
            actor_role="user",
            action=ACTION_CHARGE_CREATE,
            entity_type="charge",
            entity_id=charge.id,
        )
        return charge

    async def list_active_by_user(self, user_id: int) -> list[Charge]:
        """Список активных списаний пользователя, отсортированный по next_date."""
        result = await self._session.execute(
            select(Charge)
            .where(Charge.user_id == user_id, Charge.status == "active")
            .order_by(Charge.next_date, Charge.id)
        )
        return list(result.scalars().all())

    async def list_active_grouped_by_category(self, user_id: int) -> dict[int | None, list[Charge]]:
        """Активные списания, сгруппированные по category_id (None = без категории).
        Внутри группы отсортированы по next_date (для TASK-0041)."""
        charges = await self.list_active_by_user(user_id)
        groups: dict[int | None, list[Charge]] = defaultdict(list)
        for c in charges:
            groups[c.category_id].append(c)
        for k in groups:
            groups[k].sort(key=lambda c: c.next_date or date(9999, 1, 1))
        return dict(groups)

    async def get(self, user_id: int, charge_id: int) -> Charge | None:
        """Получить списание по ID с проверкой владельца."""
        result = await self._session.execute(
            select(Charge).where(Charge.user_id == user_id, Charge.id == charge_id)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: int, charge_id: int, **values: object) -> Charge | None:
        """Обновить поля списания (с проверкой владельца)."""
        result = await self._session.execute(
            update(Charge)
            .where(Charge.user_id == user_id, Charge.id == charge_id)
            .values(**values)
            .returning(Charge)
        )
        updated = result.scalar_one_or_none()
        if updated:
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CHARGE_EDIT,
                entity_type="charge",
                entity_id=charge_id,
            )
        return updated

    async def delete(self, user_id: int, charge_id: int) -> bool:
        """Удалить списание (с проверкой владельца)."""
        result = await self._session.execute(
            delete(Charge).where(Charge.user_id == user_id, Charge.id == charge_id)
        )
        deleted: bool = result.rowcount > 0  # type: ignore[attr-defined]
        if deleted:
            logger.info("Deleted charge: user_id=%s, charge_id=%s", user_id, charge_id)
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CHARGE_DELETE,
                entity_type="charge",
                entity_id=charge_id,
            )
        return deleted

    async def mark_paid(self, user_id: int, charge_id: int) -> Charge | None:
        """
        Отметить списание как оплаченное.

        - Для периодических: next_date = calculate_next_date(...), статус остаётся active
        - Для once: status=done, paid_at=now (UTC), запись остаётся для истории

        Returns:
            Обновлённое списание или None
        """
        charge = await self.get(user_id, charge_id)
        if not charge or charge.status != "active":
            return None

        now = datetime.now(UTC)

        if charge.period == "once":
            charge.status = "done"
            charge.paid_at = now
            logger.info(
                "Marked one-time charge as done: user_id=%s, charge_id=%s",
                user_id,
                charge_id,
            )
        else:
            new_next = calculate_next_date(charge.next_date, charge.period)  # type: ignore[arg-type]
            charge.next_date = new_next
            logger.info(
                "Marked periodic charge paid (shifted): user_id=%s, charge_id=%s, new_next=%s",
                user_id,
                charge_id,
                new_next,
            )

        await self._session.flush()
        await AuditLogRepository(self._session).record(
            actor_id=user_id,
            actor_role="user",
            action=ACTION_CHARGE_PAID,
            entity_type="charge",
            entity_id=charge_id,
        )
        return charge

    async def snooze(self, user_id: int, charge_id: int, until: date) -> Charge | None:
        """
        Отложить напоминания по списанию до указанной даты (snoozed_until).

        НЕ меняет next_date (дата платежа остаётся). По ADR-0005.
        """
        charge = await self.get(user_id, charge_id)
        if not charge:
            return None

        charge.snoozed_until = until
        await self._session.flush()
        logger.info(
            "Snoozed charge: user_id=%s, charge_id=%s, until=%s",
            user_id,
            charge_id,
            until,
        )
        await AuditLogRepository(self._session).record(
            actor_id=user_id,
            actor_role="user",
            action=ACTION_CHARGE_SNOOZE,
            entity_type="charge",
            entity_id=charge_id,
        )
        return charge
