"""
Тесты для settings handlers.

Проверка callback handlers меню настроек.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, User

from wrbot.bot.handlers import settings as settings_handler
from wrbot.bot.keyboards import get_main_menu_keyboard
from wrbot.bot.texts import Texts


@pytest.fixture
def mock_state():
    """Мок FSMContext."""
    state = AsyncMock(spec=FSMContext)
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_session():
    """Мок AsyncSession."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_settings_menu_callback():
    """Callback меню настроек."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    await settings_handler.settings_menu(callback)

    callback.message.edit_text.assert_called_once()
    assert Texts.settings_menu in callback.message.edit_text.call_args[0][0]
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_main_menu_callback():
    """Callback возврата в главное меню."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "main_menu"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    await settings_handler.main_menu(callback)

    callback.message.edit_text.assert_called_once()
    assert Texts.start_greeting in callback.message.edit_text.call_args[0][0]
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_wallets_list_empty(mock_state, mock_session):
    """Список кошельков когда пусто."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_wallets"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with (
        patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls,
        patch("wrbot.bot.handlers.settings.WalletRepository") as wallet_repo_cls,
    ):
        mock_user = MagicMock()
        mock_user.tg_id = 12345

        user_repo = AsyncMock()
        user_repo.get_or_create.return_value = mock_user
        user_repo_cls.return_value = user_repo

        wallet_repo = AsyncMock()
        wallet_repo.list_by_user.return_value = []
        wallet_repo_cls.return_value = wallet_repo

        data = {"session": mock_session}

        await settings_handler.wallets_list(callback, mock_state, **data)

        user_repo.get_or_create.assert_called_once_with(12345)
        wallet_repo.list_by_user.assert_called_once_with(12345)
        callback.message.edit_text.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_wallets_list_with_items(mock_state, mock_session):
    """Список кошельков с элементами."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_wallets"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with (
        patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls,
        patch("wrbot.bot.handlers.settings.WalletRepository") as wallet_repo_cls,
    ):
        mock_user = MagicMock()
        mock_user.tg_id = 12345

        user_repo = AsyncMock()
        user_repo.get_or_create.return_value = mock_user
        user_repo_cls.return_value = user_repo

        # Мок кошельков
        mock_wallet1 = MagicMock()
        mock_wallet1.id = 1
        mock_wallet1.name = "Тинькофф"
        mock_wallet2 = MagicMock()
        mock_wallet2.id = 2
        mock_wallet2.name = "Сбер"

        wallet_repo = AsyncMock()
        wallet_repo.list_by_user.return_value = [mock_wallet1, mock_wallet2]
        wallet_repo_cls.return_value = wallet_repo

        data = {"session": mock_session}

        await settings_handler.wallets_list(callback, mock_state, **data)

        user_repo.get_or_create.assert_called_once_with(12345)
        callback.message.edit_text.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_categories_list_empty(mock_state, mock_session):
    """Список категорий когда пусто."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_categories"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with (
        patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls,
        patch("wrbot.bot.handlers.settings.CategoryRepository") as category_repo_cls,
    ):
        mock_user = MagicMock()
        mock_user.tg_id = 12345

        user_repo = AsyncMock()
        user_repo.get_or_create.return_value = mock_user
        user_repo_cls.return_value = user_repo

        category_repo = AsyncMock()
        category_repo.list_by_user.return_value = []
        category_repo_cls.return_value = category_repo

        data = {"session": mock_session}

        await settings_handler.categories_list(callback, mock_state, **data)

        user_repo.get_or_create.assert_called_once_with(12345)
        category_repo.list_by_user.assert_called_once_with(12345)
        callback.message.edit_text.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_categories_list_with_items(mock_state, mock_session):
    """Список категорий с элементами."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_categories"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    with (
        patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls,
        patch("wrbot.bot.handlers.settings.CategoryRepository") as category_repo_cls,
    ):
        mock_user = MagicMock()
        mock_user.tg_id = 12345

        user_repo = AsyncMock()
        user_repo.get_or_create.return_value = mock_user
        user_repo_cls.return_value = user_repo

        # Мок категорий
        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.name = "Подписки"
        mock_cat2 = MagicMock()
        mock_cat2.id = 2
        mock_cat2.name = "ЖКХ"

        category_repo = AsyncMock()
        category_repo.list_by_user.return_value = [mock_cat1, mock_cat2]
        category_repo_cls.return_value = category_repo

        data = {"session": mock_session}

        await settings_handler.categories_list(callback, mock_state, **data)

        user_repo.get_or_create.assert_called_once_with(12345)
        callback.message.edit_text.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_action_callback(mock_state):
    """Callback отмены действия."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "cancel"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    await settings_handler.cancel_action(callback, mock_state)

    mock_state.clear.assert_called_once()
    callback.message.edit_text.assert_called_once_with(
        Texts.action_cancelled, reply_markup=get_main_menu_keyboard()
    )
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_command_message(mock_state):
    """Команда /cancel."""
    from aiogram.types import Message

    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()

    await settings_handler.cancel_command(message, mock_state)

    mock_state.clear.assert_called_once()
    message.answer.assert_called_once_with(
        Texts.action_cancelled, reply_markup=get_main_menu_keyboard()
    )
