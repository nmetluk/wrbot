"""
SentReminder repository.

Идемпотентная запись отправленных напоминаний (для устойчивости к рестартам и повторным тикам).
"""

import logging
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import SentReminder

logger = logging.getLogger(__name__)


class SentReminderRepository:
    """Репозиторий для отметок отправленных напоминаний."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def was_sent(self, charge_id: int, target_date: date, days_before: int) -> bool:
        """Проверить, было ли уже отправлено напоминание за days_before дней до target_date."""
        result = await self._session.execute(
            select(SentReminder.id).where(
                SentReminder.charge_id == charge_id,
                SentReminder.target_date == target_date,
                SentReminder.days_before == days_before,
            )
        )
        return result.scalar_one_or_none() is not None

    async def record(self, charge_id: int, target_date: date, days_before: int) -> bool:
        """
        Зафиксировать отправку напоминания (идемпотентно).

        Возвращает True если запись была добавлена (первая отправка),
        False если уже была (дубликат/повтор после рестарта).
        """
        # Используем INSERT OR IGNORE для SQLite (идемпотентность)
        stmt = (
            sqlite_insert(SentReminder)
            .values(
                charge_id=charge_id,
                target_date=target_date,
                days_before=days_before,
                sent_at=datetime.now(UTC),
            )
            .prefix_with("OR IGNORE")
        )

        result = await self._session.execute(stmt)
        inserted = result.rowcount > 0  # type: ignore[attr-defined]

        if inserted:
            logger.info(
                "Recorded sent reminder: charge_id=%s, target=%s, days_before=%s",
                charge_id,
                target_date,
                days_before,
            )
        else:
            logger.debug(
                "Duplicate sent reminder (idempotent): charge_id=%s, target=%s, days_before=%s",
                charge_id,
                target_date,
                days_before,
            )

        return bool(inserted)
