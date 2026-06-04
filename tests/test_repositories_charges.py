"""
Тесты для ChargeRepository (TASK-0010).

Проверка CRUD, изоляции по tg_id, mark_paid (сдвиг/закрытие), лимитов, дат.
"""

from datetime import date
from decimal import Decimal

import pytest

from wrbot.repositories.charges import ChargeRepository
from wrbot.repositories.users import UserRepository
from wrbot.services.reference import InvalidAmount, LimitExceeded


@pytest.mark.asyncio
async def test_create_charge(async_session):
    """Базовое создание списания."""
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    charge = await charge_repo.create(
        user_id=user.tg_id,
        name="Аренда",
        amount=Decimal("1500.50"),
        wallet_id=1,  # в тесте не важно, FK не проверяем строго
        category_id=None,
        next_date=date(2026, 7, 15),
        period="monthly",
    )

    assert charge.id is not None
    assert charge.user_id == user.tg_id
    assert charge.amount == Decimal("1500.50")
    assert charge.currency == "RUB"
    assert charge.period == "monthly"
    assert charge.status == "active"

    # last_currency обновляется при создании (TASK-0049)
    u = await user_repo.get(user.tg_id)
    assert u is not None
    assert u.last_currency == "RUB"


@pytest.mark.asyncio
async def test_create_charge_invalid_amount_raises(async_session):
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)

    with pytest.raises(InvalidAmount):
        await charge_repo.create(
            user_id=user.tg_id,
            name="Bad",
            amount=Decimal("0"),
            wallet_id=1,
            category_id=None,
            next_date=date(2026, 7, 1),
            period="monthly",
        )


@pytest.mark.asyncio
async def test_list_active_by_user_filters_status(async_session):
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(999, create_default_wallet=False)

    c1 = await charge_repo.create(
        user.tg_id, "Active1", Decimal("100"), 1, None, date(2026, 8, 1), "monthly"
    )
    c2 = await charge_repo.create(
        user.tg_id, "Once", Decimal("200"), 1, None, date(2026, 8, 2), "once"
    )

    # Помечаем once как paid → должно исчезнуть из active
    await charge_repo.mark_paid(user.tg_id, c2.id)

    active = await charge_repo.list_active_by_user(user.tg_id)
    assert len(active) == 1
    assert active[0].id == c1.id


@pytest.mark.asyncio
async def test_mark_paid_periodic_shifts_date(async_session):
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(777, create_default_wallet=False)
    charge = await charge_repo.create(
        user.tg_id, "Internet", Decimal("500"), 1, None, date(2026, 1, 31), "monthly"
    )

    updated = await charge_repo.mark_paid(user.tg_id, charge.id)
    assert updated is not None
    assert updated.status == "active"
    assert updated.next_date == date(2026, 2, 28)  # clamp
    assert updated.paid_at is None


@pytest.mark.asyncio
async def test_mark_paid_once_closes_it(async_session):
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(888, create_default_wallet=False)
    charge = await charge_repo.create(
        user.tg_id, "One time", Decimal("1000"), 1, None, date(2026, 12, 31), "once"
    )

    updated = await charge_repo.mark_paid(user.tg_id, charge.id)
    assert updated is not None
    assert updated.status == "done"
    assert updated.paid_at is not None
    assert updated.next_date == date(2026, 12, 31)  # не сдвинулась


@pytest.mark.asyncio
async def test_charge_isolation_by_user(async_session):
    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    u1 = await user_repo.get_or_create(111, create_default_wallet=False)
    u2 = await user_repo.get_or_create(222, create_default_wallet=False)

    c1 = await charge_repo.create(
        u1.tg_id, "U1", Decimal("10"), 1, None, date(2026, 9, 1), "monthly"
    )
    await charge_repo.create(u2.tg_id, "U2", Decimal("20"), 1, None, date(2026, 9, 2), "monthly")

    assert await charge_repo.get(u1.tg_id, c1.id) is not None
    assert await charge_repo.get(u2.tg_id, c1.id) is None  # чужое


@pytest.mark.asyncio
async def test_charge_limit_raises(async_session, monkeypatch):
    monkeypatch.setenv("MAX_CHARGES", "1")
    from wrbot.config import get_settings

    get_settings.cache_clear()

    user_repo = UserRepository(async_session)
    charge_repo = ChargeRepository(async_session)

    user = await user_repo.get_or_create(555, create_default_wallet=False)

    await charge_repo.create(
        user.tg_id, "First", Decimal("100"), 1, None, date(2026, 10, 1), "monthly"
    )

    with pytest.raises(LimitExceeded, match="лимит списаний"):
        await charge_repo.create(
            user.tg_id, "Second", Decimal("200"), 1, None, date(2026, 10, 2), "monthly"
        )
