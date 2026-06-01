"""
Тесты для categories handlers.

Проверка callback и message handlers с моками репозиториев.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from wrbot.bot.handlers import categories as categories_handler
from wrbot.bot.states import CategoryStates


@pytest.fixture
def mock_state():
    """Мок FSMContext."""
    state = AsyncMock(spec=FSMContext)
    state_data = {}
    state.get_data.return_value = state_data
    state.update_data.side_effect = lambda **kwargs: state_data.update(kwargs)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_session():
    """Мок AsyncSession."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_category_details_callback():
    """Callback с деталями категории."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "category_42"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    await categories_handler.category_details(callback)

    callback.message.edit_reply_markup.assert_called_once()
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_category_add_start(mock_state, mock_session):
    """Начало добавления категории."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "category_add"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    data = {"session": mock_session}

    await categories_handler.category_add_start(callback, mock_state, **data)

    mock_state.update_data.assert_called_once()
    mock_state.set_state.assert_called_once_with(CategoryStates.name)
    callback.message.edit_text.assert_called_once()
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_category_rename_start(mock_state, mock_session):
    """Начало переименования категории."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "category_rename_42"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    # Мок категории
    mock_category = MagicMock()
    mock_category.id = 42
    mock_category.name = "Старое имя"

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_category
        mock_repo_class.return_value = mock_repo

        handler_data = {"session": mock_session}

        await categories_handler.category_rename_start(callback, mock_state, **handler_data)

        mock_state.update_data.assert_called_once()
        mock_repo.get.assert_called_once_with(12345, 42)
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_category_delete_confirm(mock_state, mock_session):
    """Подтверждение удаления категории."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "category_delete_42"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    # Мок категории
    mock_category = MagicMock()
    mock_category.id = 42
    mock_category.name = "Тест"

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_category
        mock_repo_class.return_value = mock_repo

        handler_data = {"session": mock_session}

        await categories_handler.category_delete_confirm(callback, mock_state, **handler_data)

        mock_state.update_data.assert_called_once_with(category_id=42)
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_category_delete_success(mock_state, mock_session):
    """Успешное удаление категории."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_repo.list_by_user.return_value = []
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "category_id": 42,
            "session": mock_session,
        }

        await categories_handler.category_delete(callback, mock_state)

        mock_repo.delete.assert_called_once_with(12345, 42)
        mock_state.clear.assert_called_once()
        # edit_text вызывается как минимум один раз
        assert callback.message.edit_text.call_count >= 1


@pytest.mark.asyncio
async def test_category_delete_not_found(mock_state, mock_session):
    """Удаление несуществующей категории."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "category_id": 42,
            "session": mock_session,
        }

        await categories_handler.category_delete(callback, mock_state)

        callback.answer.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_create(mock_state, mock_session):
    """Создание категории через ввод названия."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "Новая категория"
    message.from_user = tg_user
    message.answer = AsyncMock()

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_category = MagicMock()
        mock_category.id = 1
        mock_category.name = "Новая категория"

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_category
        mock_repo.list_by_user.return_value = [mock_category]
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "session": mock_session,
            "category_id": None,
        }

        await categories_handler.category_name_handler(message, mock_state)

        mock_repo.create.assert_called_once_with(12345, "Новая категория")
        message.answer.assert_called()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_rename(mock_state, mock_session):
    """Переименование категории через ввод названия."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "Новое имя"
    message.from_user = tg_user
    message.answer = AsyncMock()

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_category = MagicMock()
        mock_category.id = 42
        mock_category.name = "Новое имя"

        mock_repo = AsyncMock()
        mock_repo.rename.return_value = mock_category
        mock_repo.list_by_user.return_value = [mock_category]
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "session": mock_session,
            "category_id": 42,
        }

        await categories_handler.category_name_handler(message, mock_state)

        mock_repo.rename.assert_called_once_with(12345, 42, "Новое имя")
        message.answer.assert_called()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_empty_name(mock_state, mock_session):
    """Пустое название вызывает ошибку."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "   "
    message.from_user = tg_user
    message.answer = AsyncMock()

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "session": mock_session,
            "category_id": None,
        }

        await categories_handler.category_name_handler(message, mock_state)

        # Проверка, что был хотя бы один вызов answer
        message.answer.assert_called()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_duplicate_name(mock_state, mock_session):
    """Дубликат имени вызывает ошибку."""
    from wrbot.services.reference import DuplicateName

    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "Дубль"
    message.from_user = tg_user
    message.answer = AsyncMock()

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = DuplicateName("уже существует")
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "session": mock_session,
            "category_id": None,
        }

        await categories_handler.category_name_handler(message, mock_state)

        # Проверка, что было отправлено сообщение об ошибке дубля
        assert any("уже существует" in str(call.args[0]) for call in message.answer.call_args_list)
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_limit_exceeded(mock_state, mock_session):
    """Превышение лимита вызывает ошибку."""
    from wrbot.services.reference import LimitExceeded

    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "Ещё одна"
    message.from_user = tg_user
    message.answer = AsyncMock()

    with patch("wrbot.bot.handlers.categories.CategoryRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = LimitExceeded("превышен лимит")
        mock_repo_class.return_value = mock_repo

        mock_state.get_data.return_value = {
            "session": mock_session,
            "category_id": None,
        }

        await categories_handler.category_name_handler(message, mock_state)

        # Проверка, что было отправлено сообщение об ошибке лимита
        assert any("лимит" in str(call.args[0]) or "Превышен" in str(call.args[0]) for call in message.answer.call_args_list)
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_category_name_handler_no_session(mock_state):
    """Отсутствие сессии вызывает ошибку и очищает состояние."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    message = AsyncMock(spec=Message)
    message.text = "Тест"
    message.from_user = tg_user
    message.answer = AsyncMock()

    mock_state.get_data.return_value = {
        "session": None,
        "category_id": None,
    }

    await categories_handler.category_name_handler(message, mock_state)

    message.answer.assert_called_once()
    mock_state.clear.assert_called_once()
