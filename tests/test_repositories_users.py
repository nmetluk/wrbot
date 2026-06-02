"""
Тесты для UserRepository.

Проверка get_or_create, изоляции, идемпотентности.
"""

import pytest

from wrbot.repositories.users import UserRepository


@pytest.mark.asyncio
async def test_get_or_create_creates_new_user(async_session):
    """get_or_create создаёт нового пользователя с дефолтами."""
    repo = UserRepository(async_session)

    user = await repo.get_or_create(12345)

    assert user.tg_id == 12345
    assert user.notify_time.isoformat() == "10:00:00"
    assert user.tz == "Europe/Moscow"
    assert user.global_days == "[5,3,1]"


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(async_session):
    """get_or_create идемпотентен: повторный вызов возвращает того же пользователя."""
    repo = UserRepository(async_session)

    user1 = await repo.get_or_create(12345)
    user2 = await repo.get_or_create(12345)

    assert user1.tg_id == user2.tg_id == 12345
    assert user1 is user2  # Один и тот же объект


@pytest.mark.asyncio
async def test_get_or_create_custom_defaults(async_session):
    """get_or_create принимает кастомные дефолты."""
    from datetime import time

    repo = UserRepository(async_session)

    user = await repo.get_or_create(
        99999,
        notify_time=time(9, 30),
        tz="America/New_York",
        global_days="[1]",
    )

    assert user.tg_id == 99999
    assert user.notify_time.isoformat() == "09:30:00"
    assert user.tz == "America/New_York"
    assert user.global_days == "[1]"


@pytest.mark.asyncio
async def test_different_users_are_isolated(async_session):
    """Разные пользователи не пересекаются."""
    repo = UserRepository(async_session)

    user1 = await repo.get_or_create(11111)
    user2 = await repo.get_or_create(22222)

    assert user1.tg_id == 11111
    assert user2.tg_id == 22222
    assert user1 is not user2  # Разные объекты


@pytest.mark.asyncio
async def test_set_notify_time_updates(async_session):
    """set_notify_time сохраняет новое время и доступно через get."""
    from datetime import time

    from wrbot.repositories.users import UserRepository

    repo = UserRepository(async_session)
    await repo.get_or_create(12345)  # дефолт 10:00

    updated = await repo.set_notify_time(12345, time(8, 30))
    assert updated is not None
    assert updated.notify_time.isoformat() == "08:30:00"

    user = await repo.get(12345)
    assert user is not None
    assert user.notify_time.isoformat() == "08:30:00"


@pytest.mark.asyncio
async def test_set_global_days_updates(async_session):
    """set_global_days сохраняет JSON (в т.ч. [] для выключения)."""
    from wrbot.repositories.users import UserRepository

    repo = UserRepository(async_session)
    await repo.get_or_create(12345)

    import json

    updated = await repo.set_global_days(12345, "[7,1]")
    assert updated is not None
    # json.dumps даёт компактно без пробела после запятой в этом окружении
    assert updated.global_days in (json.dumps([7, 1]), "[7,1]", "[7, 1]")

    user = await repo.get(12345)
    assert user is not None
    assert user.global_days in (json.dumps([7, 1]), "[7,1]", "[7, 1]")

    # выключить
    await repo.set_global_days(12345, "[]")
    user2 = await repo.get(12345)
    assert user2.global_days == "[]"


@pytest.mark.asyncio
async def test_get_or_create_creates_default_wallet(async_session):
    """get_or_create создаёт дефолтный «Основная карта» для нового юзера (TASK-0035)."""
    from wrbot.repositories.wallets import WalletRepository

    repo = UserRepository(async_session)
    wrepo = WalletRepository(async_session)

    await repo.get_or_create(12345)
    ws = await wrepo.list_by_user(12345)
    assert len(ws) == 1
    assert ws[0].name == "Основная карта"
    assert ws[0].user_id == 12345


@pytest.mark.asyncio
async def test_get_or_create_does_not_recreate_wallet_after_delete(async_session):
    """Дефолт не пересоздаётся после удаления (TASK-0035)."""
    from wrbot.repositories.wallets import WalletRepository

    repo = UserRepository(async_session)
    wrepo = WalletRepository(async_session)

    await repo.get_or_create(99999)
    ws = await wrepo.list_by_user(99999)
    assert len(ws) == 1
    default_id = ws[0].id
    assert ws[0].name == "Основная карта"

    # Удаляем
    deleted = await wrepo.delete(99999, default_id)
    assert deleted is True
    ws_after = await wrepo.list_by_user(99999)
    assert ws_after == []

    # Повторный get_or_create — кошелёк не появляется
    await repo.get_or_create(99999)
    ws_final = await wrepo.list_by_user(99999)
    assert ws_final == []
