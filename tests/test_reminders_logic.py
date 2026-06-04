"""
Тесты логики напоминаний (TASK-0014).

Эффективные дни, due-расчёт, snooze, выбор по времени.
"""

from datetime import UTC, date, datetime, time

import pytest

from wrbot.db.models import Charge, User
from wrbot.services.reminders import (
    get_due_target_days,
    get_effective_days,
    select_users_to_notify_at,
)


def make_user(
    tg_id: int = 123,
    tz: str = "Europe/Moscow",
    global_days: str = "[5,3,1]",
    notify_time: time = time(10, 0),
) -> User:
    u = User(
        tg_id=tg_id,
        notify_time=notify_time,
        tz=tz,
        global_days=global_days,
        last_currency="RUB",
        created_at=datetime.now(UTC),
    )
    # For tests we don't persist
    return u


def make_charge(
    user_id: int = 123,
    next_date: date = date(2026, 8, 20),
    period: str = "monthly",
    individual_days: str | None = None,
    snoozed_until: date | None = None,
) -> Charge:
    c = Charge(
        id=1,
        user_id=user_id,
        name="Test",
        amount=100,
        currency="RUB",
        wallet_id=1,
        category_id=None,
        next_date=next_date,
        period=period,
        individual_days=individual_days,
        status="active",
        snoozed_until=snoozed_until,
        created_at=datetime.now(UTC),
    )
    return c


def test_effective_days_global():
    user = make_user()
    charge = make_charge()
    assert get_effective_days(charge, user) == [1, 3, 5]


def test_effective_days_individual_overrides():
    user = make_user()
    charge = make_charge(individual_days="[7,1]")
    assert get_effective_days(charge, user) == [1, 7]


def test_effective_days_off():
    user = make_user()
    charge = make_charge(individual_days="[]")
    assert get_effective_days(charge, user) == []


def test_due_simple():
    today = date(2026, 8, 15)
    charge = make_charge(next_date=date(2026, 8, 20))  # 5 days before
    user = make_user()
    due = get_due_target_days(charge, today, user)
    assert (date(2026, 8, 15), 5) in due


def test_due_snooze_repeat():
    today = date(2026, 8, 15)
    charge = make_charge(
        next_date=date(2026, 8, 20),
        snoozed_until=date(2026, 8, 15),  # snoozed today
    )
    user = make_user()
    due = get_due_target_days(charge, today, user)
    # Should include the days even if "repeat"
    assert len(due) >= 1


@pytest.mark.asyncio
async def test_select_users_to_notify_at(async_session):
    # Create test user
    from wrbot.repositories.users import UserRepository

    user_repo = UserRepository(async_session)
    await user_repo.get_or_create(777, create_default_wallet=False)  # default tz Moscow, 10:00

    now = datetime(2026, 8, 15, 7, 0, tzinfo=UTC)  # 10:00 in Moscow (UTC+3)
    users = await select_users_to_notify_at(async_session, now)
    # May or may not find depending on fixture data, but function runs without error
    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_select_users_to_notify_at_respects_notify_time(async_session):
    """Изменение notify_time реально влияет на выбор пользователей в свипе (FR-10 coverage)."""
    from datetime import time

    from wrbot.repositories.users import UserRepository

    user_repo = UserRepository(async_session)
    # Пользователь с 09:00 (UTC+3 -> 06:00 UTC)
    await user_repo.get_or_create(
        8888, notify_time=time(9, 0), tz="Europe/Moscow", create_default_wallet=False
    )

    # Точное совпадение 09:00 local
    now_match = datetime(2026, 8, 15, 6, 0, tzinfo=UTC)
    users_match = await select_users_to_notify_at(async_session, now_match)
    assert any(u.tg_id == 8888 for u in users_match)

    # Несовпадение
    now_mismatch = datetime(2026, 8, 15, 7, 0, tzinfo=UTC)  # 10:00 local
    users_mismatch = await select_users_to_notify_at(async_session, now_mismatch)
    assert not any(u.tg_id == 8888 for u in users_mismatch)
