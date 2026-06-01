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
