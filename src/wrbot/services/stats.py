"""
Statistics for admin summary (M6, TASK-0033) and daily dashboard (TASK-0034).

Краткая сводка (hourly) + расширенные метрики для дашборда 21:00:
рост пользователей, daily active/new (по audit), charges, периоды, топ-категории,
напоминания и ошибки (из audit_log).
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import AuditLog, Charge, User
from wrbot.repositories.audit_log import ACTION_ERROR, ACTION_REMINDER_SENT

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


# --- TASK-0034 daily dashboard metrics (use audit_log where specified) ---


async def get_user_growth_30d(
    session: AsyncSession, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Рост пользователей накопительно за 30 дней (линия).
    Возвращает [{'date': date, 'cumulative': int}, ...]
    """
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=29)
    cutoff = datetime.combine(start_date, datetime.min.time())

    created_ats = await session.scalars(select(User.created_at).where(User.created_at >= cutoff))
    by_day: dict[date, int] = defaultdict(int)
    for ca in created_ats:
        d = ca.date() if isinstance(ca, datetime) else ca
        if isinstance(d, date):
            by_day[d] += 1

    result: list[dict[str, Any]] = []
    cum = 0
    for i in range(30):
        d = start_date + timedelta(days=i)
        cum += by_day.get(d, 0)
        result.append({"date": d, "cumulative": cum})
    return result


async def get_daily_new_and_active_users(
    session: AsyncSession, days: int = 7, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Новые (users.created_at) + активные (distinct по audit, role=user) за N дней."""
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=days - 1)
    cutoff = datetime.combine(start_date, datetime.min.time())

    # new users per day
    new_rows = await session.execute(
        select(func.date(User.created_at).label("d"), func.count().label("new"))
        .where(User.created_at >= cutoff)
        .group_by(func.date(User.created_at))
    )
    new_by_day: dict[str, int] = {str(r.d): r.new for r in new_rows}

    # active = distinct actors from audit in period (user role preferred)
    audit_rows = await session.execute(
        select(
            func.date(AuditLog.created_at).label("d"),
            func.count(AuditLog.actor_id.distinct()).label("active"),
        )
        .where(AuditLog.created_at >= cutoff)
        .where(AuditLog.actor_role == "user")
        .group_by(func.date(AuditLog.created_at))
    )
    active_by_day: dict[str, int] = {str(r.d): r.active for r in audit_rows}

    result: list[dict[str, Any]] = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        ds = d.isoformat()
        result.append(
            {
                "date": d,
                "new": new_by_day.get(ds, 0),
                "active": active_by_day.get(ds, 0),
            }
        )
    return result


async def get_charges_created_daily(
    session: AsyncSession, days: int = 14, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Создано списаний за день (14 дней) — для бар-чарта."""
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=days - 1)
    cutoff = datetime.combine(start_date, datetime.min.time())

    rows = await session.execute(
        select(func.date(Charge.created_at).label("d"), func.count().label("cnt"))
        .where(Charge.created_at >= cutoff)
        .group_by(func.date(Charge.created_at))
        .order_by("d")
    )
    by_day = {str(r.d): r.cnt for r in rows}
    result = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        result.append({"date": d, "count": by_day.get(d.isoformat(), 0)})
    return result


async def get_payments_daily(
    session: AsyncSession, days: int = 7, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Отмечено оплат за день: кол-во + сумма (по paid_at или done recent)."""
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=days - 1)
    cutoff = datetime.combine(start_date, datetime.min.time())

    # count and sum(amount) where paid_at in range or (done and created recent fallback)
    rows = await session.execute(
        select(
            func.date(Charge.paid_at).label("d"),
            func.count().label("cnt"),
            func.sum(Charge.amount).label("total"),
        )
        .where(Charge.paid_at >= cutoff)
        .group_by(func.date(Charge.paid_at))
    )
    by_day: dict[str, dict[str, Any]] = {}
    for r in rows:
        ds = str(r.d)
        by_day[ds] = {"count": r.cnt or 0, "sum": float(r.total or 0)}

    # fallback for done without paid_at? limited
    result = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        ds = d.isoformat()
        entry = by_day.get(ds, {"count": 0, "sum": 0.0})
        result.append({"date": d, "count": entry["count"], "sum": entry["sum"]})
    return result


async def get_period_distribution(session: AsyncSession) -> dict[str, int]:
    """Распределение активных списаний по period (для pie)."""
    rows = await session.execute(
        select(Charge.period, func.count().label("cnt"))
        .where(Charge.status == "active")
        .group_by(Charge.period)
    )
    return {(r.period or "unknown"): r.cnt for r in rows}


async def get_top_categories(
    session: AsyncSession, limit: int = 5, by: str = "count"
) -> list[dict[str, Any]]:
    """Топ категорий по числу или сумме активных списаний (horizontal bar)."""
    # join category name
    from wrbot.db.models import Category  # local to avoid cycle if any

    order = func.sum(Charge.amount).desc() if by == "sum" else func.count().desc()

    stmt = (
        select(
            Category.name.label("cat"),
            func.count().label("count"),
            func.sum(Charge.amount).label("total"),
        )
        .join(Category, Charge.category_id == Category.id, isouter=True)
        .where(Charge.status == "active")
        .group_by(Category.name)
        .order_by(order)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {"name": (r.cat or "Без категории"), "count": r.count, "total": float(r.total or 0)}
        for r in rows
    ]


async def get_reminders_sent_daily(
    session: AsyncSession, days: int = 7, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Отправлено напоминаний за день (из audit_log action=reminder.sent)."""
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=days - 1)
    cutoff = datetime.combine(start_date, datetime.min.time())

    rows = await session.execute(
        select(func.date(AuditLog.created_at).label("d"), func.count().label("cnt"))
        .where(AuditLog.created_at >= cutoff)
        .where(AuditLog.action == ACTION_REMINDER_SENT)
        .group_by(func.date(AuditLog.created_at))
    )
    by_day = {str(r.d): r.cnt for r in rows}
    result = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        result.append({"date": d, "count": by_day.get(d.isoformat(), 0)})
    return result


async def get_errors_daily(
    session: AsyncSession, days: int = 7, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Ошибки за день (из audit_log action=error.critical, error-hook)."""
    if now is None:
        now = datetime.now()
    start_date = now.date() - timedelta(days=days - 1)
    cutoff = datetime.combine(start_date, datetime.min.time())

    rows = await session.execute(
        select(func.date(AuditLog.created_at).label("d"), func.count().label("cnt"))
        .where(AuditLog.created_at >= cutoff)
        .where(AuditLog.action == ACTION_ERROR)
        .group_by(func.date(AuditLog.created_at))
    )
    by_day = {str(r.d): r.cnt for r in rows}
    result = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        result.append({"date": d, "count": by_day.get(d.isoformat(), 0)})
    return result
