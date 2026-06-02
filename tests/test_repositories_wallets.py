"""
Тесты для WalletRepository.

Проверка CRUD, изоляции, лимитов, валидации.
"""

import pytest

from wrbot.repositories.users import UserRepository
from wrbot.repositories.wallets import WalletRepository
from wrbot.services.reference import DuplicateName, InvalidName, LimitExceeded


@pytest.mark.asyncio
async def test_create_wallet(async_session):
    """Создание кошелька."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    wallet = await wallet_repo.create(user.tg_id, "Наличные")

    assert wallet.id is not None
    assert wallet.user_id == user.tg_id
    assert wallet.name == "Наличные"


@pytest.mark.asyncio
async def test_create_wallet_trims_name(async_session):
    """Имя кошелька обрезается по краям."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    wallet = await wallet_repo.create(user.tg_id, "  Точка  ")

    assert wallet.name == "Точка"


@pytest.mark.asyncio
async def test_create_wallet_empty_name_raises(async_session):
    """Пустое имя вызывает InvalidName."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)

    with pytest.raises(InvalidName, match="пуст"):
        await wallet_repo.create(user.tg_id, "   ")


@pytest.mark.asyncio
async def test_create_wallet_duplicate_name_raises(async_session):
    """Дубликат имени вызывает DuplicateName."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    await wallet_repo.create(user.tg_id, "Карта")

    with pytest.raises(DuplicateName, match="Карта"):
        await wallet_repo.create(user.tg_id, "Карта")


@pytest.mark.asyncio
async def test_create_wallet_limit_raises(async_session, monkeypatch):
    """Превышение лимита вызывает LimitExceeded."""

    # Установим лимит в 2 для теста
    monkeypatch.setenv("MAX_WALLETS", "2")

    from wrbot.config import get_settings

    get_settings.cache_clear()

    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    await wallet_repo.create(user.tg_id, "w1")
    await wallet_repo.create(user.tg_id, "w2")

    with pytest.raises(LimitExceeded, match="лимит"):
        await wallet_repo.create(user.tg_id, "w3")


@pytest.mark.asyncio
async def test_list_by_user(async_session):
    """Список кошельков пользователя."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user1 = await user_repo.get_or_create(11111, create_default_wallet=False)
    user2 = await user_repo.get_or_create(22222, create_default_wallet=False)

    await wallet_repo.create(user1.tg_id, "Альфа")
    await wallet_repo.create(user1.tg_id, "Бета")
    await wallet_repo.create(user2.tg_id, "Гамма")  # Чужой

    wallets = await wallet_repo.list_by_user(user1.tg_id)

    assert len(wallets) == 2
    names = [w.name for w in wallets]
    assert names == ["Альфа", "Бета"]


@pytest.mark.asyncio
async def test_list_sorted_by_name(async_session):
    """Список сортируется по имени."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    await wallet_repo.create(user.tg_id, "Zulu")
    await wallet_repo.create(user.tg_id, "Alpha")

    wallets = await wallet_repo.list_by_user(user.tg_id)

    assert [w.name for w in wallets] == ["Alpha", "Zulu"]


@pytest.mark.asyncio
async def test_get_own_wallet(async_session):
    """Получение своего кошелька."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    created = await wallet_repo.create(user.tg_id, "Сбербанк")

    fetched = await wallet_repo.get(user.tg_id, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Сбербанк"


@pytest.mark.asyncio
async def test_get_other_users_wallet_returns_none(async_session):
    """Получение чужого кошелька возвращает None."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user1 = await user_repo.get_or_create(11111, create_default_wallet=False)
    user2 = await user_repo.get_or_create(22222, create_default_wallet=False)

    wallet = await wallet_repo.create(user1.tg_id, "Тинькофф")

    fetched = await wallet_repo.get(user2.tg_id, wallet.id)

    assert fetched is None


@pytest.mark.asyncio
async def test_rename_wallet(async_session):
    """Переименование кошелька."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    wallet = await wallet_repo.create(user.tg_id, "Старое")

    updated = await wallet_repo.rename(user.tg_id, wallet.id, "Новое")

    assert updated is not None
    assert updated.name == "Новое"


@pytest.mark.asyncio
async def test_rename_duplicate_name_raises(async_session):
    """Переименование в занятое имя вызывает DuplicateName."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    await wallet_repo.create(user.tg_id, "Раз")
    w2 = await wallet_repo.create(user.tg_id, "Два")

    with pytest.raises(DuplicateName):
        await wallet_repo.rename(user.tg_id, w2.id, "Раз")


@pytest.mark.asyncio
async def test_delete_wallet(async_session):
    """Удаление кошелька."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user = await user_repo.get_or_create(12345, create_default_wallet=False)
    wallet = await wallet_repo.create(user.tg_id, "ВТБ")

    deleted = await wallet_repo.delete(user.tg_id, wallet.id)

    assert deleted is True
    assert await wallet_repo.get(user.tg_id, wallet.id) is None


@pytest.mark.asyncio
async def test_delete_other_users_wallet_returns_false(async_session):
    """Удаление чужого кошелька возвращает False."""
    user_repo = UserRepository(async_session)
    wallet_repo = WalletRepository(async_session)

    user1 = await user_repo.get_or_create(11111, create_default_wallet=False)
    user2 = await user_repo.get_or_create(22222, create_default_wallet=False)

    wallet = await wallet_repo.create(user1.tg_id, "Газпром")

    deleted = await wallet_repo.delete(user2.tg_id, wallet.id)

    assert deleted is False
