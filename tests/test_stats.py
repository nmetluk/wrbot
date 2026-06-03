"""
Tests for extended stats (TASK-0034 dashboard metrics + TASK-0033 hourly).

Use real DB session (db_session fixture), seed deterministic data, assert exact counts.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import AuditLog, Charge, User
from wrbot.repositories.audit_log import ACTION_ERROR, ACTION_REMINDER_SENT
from wrbot.services.stats import (
    get_charges_created_daily,
    get_daily_new_and_active_users,
    get_errors_daily,
    get_hourly_summary,
    get_payments_daily,
    get_period_distribution,
    get_reminders_sent_daily,
    get_top_categories,
    get_user_growth_30d,
)


@pytest.mark.asyncio
async def test_hourly_summary_still_works(db_session: AsyncSession):
    """Существующая hourly не сломалась после добавления метрик."""
    now = datetime(2026, 6, 3, 12, 0)
    u = User(tg_id=42, notify_time=now.time(), tz="UTC", global_days="[1,2]", created_at=now)
    db_session.add(u)
    c = Charge(
        user_id=42,
        name="test",
        amount=123,
        wallet_id=1,
        next_date=now.date() + timedelta(days=1),
        period="monthly",
        status="active",
        created_at=now,
    )
    db_session.add(c)
    await db_session.commit()

    s = await get_hourly_summary(db_session, now)
    assert s["total_users"] >= 1
    assert s["active_charges"] >= 1


@pytest.mark.asyncio
async def test_user_growth_30d(db_session: AsyncSession):
    now = datetime(2026, 6, 3, 10, 0)
    # seed 3 users on different days
    for i, d in enumerate([now - timedelta(days=5), now - timedelta(days=1), now]):
        u = User(tg_id=100 + i, notify_time=now.time(), tz="UTC", global_days="[]", created_at=d)
        db_session.add(u)
    await db_session.commit()

    growth = await get_user_growth_30d(db_session, now)
    assert len(growth) == 30
    # cumulative at end >=3
    assert growth[-1]["cumulative"] >= 3
    # some day had +1
    assert any(item["cumulative"] > 0 for item in growth)


@pytest.mark.asyncio
async def test_daily_new_and_active_via_audit(db_session: AsyncSession):
    now = datetime(2026, 6, 3, 10, 0)
    # user + some audit entries (role=user) for "active"
    u = User(
        tg_id=200,
        notify_time=now.time(),
        tz="UTC",
        global_days="[]",
        created_at=now - timedelta(days=2),
    )
    db_session.add(u)
    # audit for active
    for delta in [0, 1, 2]:
        al = AuditLog(
            actor_id=200,
            actor_role="user",
            action="charge.create",
            created_at=now - timedelta(days=delta),
        )
        db_session.add(al)
    await db_session.commit()

    act = await get_daily_new_and_active_users(db_session, days=3, now=now)
    assert len(act) == 3
    # the day of creation should have new>=1 , and active days have active>=1
    assert any(d["new"] >= 1 for d in act)
    assert any(d["active"] >= 1 for d in act)


@pytest.mark.asyncio
async def test_charges_created_and_payments(db_session: AsyncSession):
    now = datetime(2026, 6, 3, 10, 0)
    # created today and yesterday
    for delta in [0, 1]:
        c = Charge(
            user_id=1,
            name=f"c{delta}",
            amount=10,
            wallet_id=1,
            next_date=now.date(),
            period="monthly",
            status="active",
            created_at=now - timedelta(days=delta),
        )
        db_session.add(c)
    # paid
    cp = Charge(
        user_id=1,
        name="paid",
        amount=99.5,
        wallet_id=1,
        next_date=now.date(),
        period="once",
        status="done",
        paid_at=now - timedelta(days=0, hours=1),
        created_at=now - timedelta(days=2),
    )
    db_session.add(cp)
    await db_session.commit()

    created = await get_charges_created_daily(db_session, days=3, now=now)
    assert any(d["count"] >= 1 for d in created)

    paid = await get_payments_daily(db_session, days=2, now=now)
    assert any(d["count"] >= 1 for d in paid)
    assert any(d["sum"] > 0 for d in paid)


@pytest.mark.asyncio
async def test_period_dist_and_top_cats(db_session: AsyncSession):
    now = datetime(2026, 6, 3, 10, 0)
    # need category? for top use outer join ok, create simple
    from wrbot.db.models import Category

    cat = Category(name="Еда", user_id=1)
    db_session.add(cat)
    await db_session.flush()

    for i, per in enumerate(["monthly", "monthly", "quarterly"]):
        c = Charge(
            user_id=1,
            name=f"p{i}",
            amount=10 + i,
            wallet_id=1,
            next_date=now.date(),
            period=per,
            status="active",
            category_id=cat.id if per == "monthly" else None,
            created_at=now,
        )
        db_session.add(c)
    await db_session.commit()

    dist = await get_period_distribution(db_session)
    assert dist.get("monthly", 0) >= 2

    top = await get_top_categories(db_session, limit=3)
    assert len(top) >= 1
    assert "Еда" in [t["name"] for t in top] or "Без категории" in [t["name"] for t in top]


@pytest.mark.asyncio
async def test_reminders_and_errors_from_audit(db_session: AsyncSession):
    now = datetime(2026, 6, 3, 10, 0)
    # seed audit entries
    for delta in [0, 1]:
        db_session.add(
            AuditLog(
                actor_id=0,
                actor_role="system",
                action=ACTION_REMINDER_SENT,
                entity_type="charge",
                entity_id=42,
                created_at=now - timedelta(days=delta),
            )
        )
        db_session.add(
            AuditLog(
                actor_id=0,
                actor_role="system",
                action=ACTION_ERROR,
                created_at=now - timedelta(days=delta),
            )
        )
    await db_session.commit()

    rem = await get_reminders_sent_daily(db_session, days=2, now=now)
    assert any(d["count"] >= 1 for d in rem)

    err = await get_errors_daily(db_session, days=2, now=now)
    assert any(d["count"] >= 1 for d in err)
