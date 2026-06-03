"""
Statistics for admin summary (M6, TASK-0033).

Краткая сводка: пользователи, активные списания, создано/отмечено за час.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import Charge, User

logger = logging.getLogger(__name__)


async def get_hourly_summary(session: AsyncSession, now: datetime | None = None) -> dict[str, int]:
    """
    Возвращает словарь с краткой сводкой для админ-канала.

    - total_users: всего пользователей
    - active_charges: активных списаний
    - charges_created_last_hour: создано за последний час
    - charges_paid_last_hour: отмечено оплаченными за последний час (paid_at или статус)
    """
    if now is None:
        now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    # total users
    total_users = await session.scalar(select(func.count()).select_from(User))

    # active charges
    active_charges = await session.scalar(
        select(func.count()).select_from(Charge).where(Charge.status == "active")
    )

    # created last hour
    created_last_hour = await session.scalar(
        select(func.count()).select_from(Charge).where(Charge.created_at >= one_hour_ago)
    )

    # paid last hour: either status done with paid_at recent, or for periodic just the mark
    # use paid_at if set, else for done
    paid_last_hour = await session.scalar(
        select(func.count())
        .select_from(Charge)
        .where(
            (Charge.paid_at >= one_hour_ago)
            | ((Charge.status == "done") & (Charge.created_at >= one_hour_ago))  # fallback
        )
    )

    return {
        "total_users": total_users or 0,
        "active_charges": active_charges or 0,
        "charges_created_last_hour": created_last_hour or 0,
        "charges_paid_last_hour": paid_last_hour or 0,
    }
