"""
Тесты для CategoryRepository.

Проверка CRUD, изоляции, лимитов, валидации.
"""

import pytest

from wrbot.repositories.categories import CategoryRepository
from wrbot.repositories.users import UserRepository
from wrbot.services.reference import DuplicateName, InvalidName, LimitExceeded


@pytest.mark.asyncio
async def test_create_category(async_session):
    """Создание категории."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    category = await category_repo.create(user.tg_id, "Еда")

    assert category.id is not None
    assert category.user_id == user.tg_id
    assert category.name == "Еда"


@pytest.mark.asyncio
async def test_create_category_trims_name(async_session):
    """Имя категории обрезается по краям."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    category = await category_repo.create(user.tg_id, "  Транспорт  ")

    assert category.name == "Транспорт"


@pytest.mark.asyncio
async def test_create_category_empty_name_raises(async_session):
    """Пустое имя вызывает InvalidName."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)

    with pytest.raises(InvalidName, match="пуст"):
        await category_repo.create(user.tg_id, "   ")


@pytest.mark.asyncio
async def test_create_category_duplicate_name_raises(async_session):
    """Дубликат имени вызывает DuplicateName."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    await category_repo.create(user.tg_id, "Подписки")

    with pytest.raises(DuplicateName, match="Подписки"):
        await category_repo.create(user.tg_id, "Подписки")


@pytest.mark.asyncio
async def test_create_category_limit_raises(async_session, monkeypatch):
    """Превышение лимита вызывает LimitExceeded."""
    monkeypatch.setenv("MAX_CATEGORIES", "2")

    from wrbot.config import get_settings

    get_settings.cache_clear()

    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    await category_repo.create(user.tg_id, "c1")
    await category_repo.create(user.tg_id, "c2")

    with pytest.raises(LimitExceeded, match="лимит"):
        await category_repo.create(user.tg_id, "c3")


@pytest.mark.asyncio
async def test_list_by_user(async_session):
    """Список категорий пользователя."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user1 = await user_repo.get_or_create(11111)
    user2 = await user_repo.get_or_create(22222)

    await category_repo.create(user1.tg_id, "Продукты")
    await category_repo.create(user1.tg_id, "Транспорт")
    await category_repo.create(user2.tg_id, "Развлечения")  # Чужая

    categories = await category_repo.list_by_user(user1.tg_id)

    assert len(categories) == 2
    names = [c.name for c in categories]
    assert names == ["Продукты", "Транспорт"]


@pytest.mark.asyncio
async def test_list_sorted_by_name(async_session):
    """Список сортируется по имени."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    await category_repo.create(user.tg_id, "Январь")
    await category_repo.create(user.tg_id, "Альфа")

    categories = await category_repo.list_by_user(user.tg_id)

    assert [c.name for c in categories] == ["Альфа", "Январь"]


@pytest.mark.asyncio
async def test_get_own_category(async_session):
    """Получение своей категории."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    created = await category_repo.create(user.tg_id, "Здоровье")

    fetched = await category_repo.get(user.tg_id, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Здоровье"


@pytest.mark.asyncio
async def test_get_other_users_category_returns_none(async_session):
    """Получение чужой категории возвращает None."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user1 = await user_repo.get_or_create(11111)
    user2 = await user_repo.get_or_create(22222)

    category = await category_repo.create(user1.tg_id, "Спорт")

    fetched = await category_repo.get(user2.tg_id, category.id)

    assert fetched is None


@pytest.mark.asyncio
async def test_rename_category(async_session):
    """Переименование категории."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    category = await category_repo.create(user.tg_id, "Старое")

    updated = await category_repo.rename(user.tg_id, category.id, "Новое")

    assert updated is not None
    assert updated.name == "Новое"


@pytest.mark.asyncio
async def test_rename_duplicate_name_raises(async_session):
    """Переименование в занятое имя вызывает DuplicateName."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    await category_repo.create(user.tg_id, "Раз")
    c2 = await category_repo.create(user.tg_id, "Два")

    with pytest.raises(DuplicateName):
        await category_repo.rename(user.tg_id, c2.id, "Раз")


@pytest.mark.asyncio
async def test_delete_category(async_session):
    """Удаление категории."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user = await user_repo.get_or_create(12345)
    category = await category_repo.create(user.tg_id, "Коммунальные")

    deleted = await category_repo.delete(user.tg_id, category.id)

    assert deleted is True
    assert await category_repo.get(user.tg_id, category.id) is None


@pytest.mark.asyncio
async def test_delete_other_users_category_returns_false(async_session):
    """Удаление чужой категории возвращает False."""
    user_repo = UserRepository(async_session)
    category_repo = CategoryRepository(async_session)

    user1 = await user_repo.get_or_create(11111)
    user2 = await user_repo.get_or_create(22222)

    category = await category_repo.create(user1.tg_id, "Питомцы")

    deleted = await category_repo.delete(user2.tg_id, category.id)

    assert deleted is False
