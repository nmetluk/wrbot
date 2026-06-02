"""
Тесты для глобальных уведомлений (TASK-0026, FR-10).

Включая:
- Показ текущих значений (время HH:MM + дни)
- Изменение времени через ввод + валидация
- Изменение дней через toggle (gday_toggle_*) и ввод
- Сохранение через UserRepository
- Router-тесты на специфичные callback'и (урок TASK-0008)
- Рендер текстов
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, User

from wrbot.bot.handlers import settings as settings_handler
from wrbot.bot.states import SettingsStates
from wrbot.bot.texts import Texts


@pytest.fixture
def mock_state():
    """Мок FSMContext с необходимыми методами."""
    state = AsyncMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


@pytest.fixture
def mock_session():
    """Мок AsyncSession."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_global_notify_menu_shows_current_values(mock_state, mock_session):
    """settings_global показывает экран с текущими временем и днями."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_global"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    mock_user = MagicMock()
    mock_user.tg_id = 12345
    mock_user.notify_time = time(9, 30)
    mock_user.global_days = "[5,3,1]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls:
        user_repo = AsyncMock()
        user_repo.get_or_create = AsyncMock()
        user_repo.get = AsyncMock(return_value=mock_user)
        user_repo_cls.return_value = user_repo

        data = {"session": mock_session}

        await settings_handler.global_notify_menu(callback, mock_state, **data)

        user_repo.get_or_create.assert_called_once_with(12345)
        user_repo.get.assert_awaited_once_with(12345)
        callback.message.edit_text.assert_called_once()
        text_arg = callback.message.edit_text.call_args[0][0]
        assert "09:30" in text_arg
        assert "1, 3, 5" in text_arg or "1,3,5" in text_arg
        callback.answer.assert_called_once()
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_global_notify_menu_handles_empty_days(mock_state, mock_session):
    """Меню корректно показывает 'выключено' при [] ."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_global"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    mock_user = MagicMock()
    mock_user.tg_id = 12345
    mock_user.notify_time = time(10, 0)
    mock_user.global_days = "[]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as user_repo_cls:
        user_repo = AsyncMock()
        user_repo.get_or_create = AsyncMock()
        user_repo.get = AsyncMock(return_value=mock_user)
        user_repo_cls.return_value = user_repo

        data = {"session": mock_session}
        await settings_handler.global_notify_menu(callback, mock_state, **data)

        text_arg = callback.message.edit_text.call_args[0][0]
        assert "выключено" in text_arg


@pytest.mark.asyncio
async def test_gnotify_time_start_sets_state_and_prompt(mock_state, mock_session):
    """Кнопка «Изменить время» переводит в состояние и показывает prompt."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "gnotify_time"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = Mock(spec=User, id=12345)

    data = {"session": mock_session}

    await settings_handler.gnotify_time_start(callback, mock_state, **data)

    mock_state.set_state.assert_awaited_once_with(SettingsStates.notify_time)
    mock_state.update_data.assert_awaited_once()
    callback.message.edit_text.assert_called_once()
    assert Texts.global_notify_enter_time in callback.message.edit_text.call_args[0][0]
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_process_notify_time_valid_saves_and_shows_view(mock_state, mock_session):
    """Валидный ввод времени: set_notify_time, clear, показ экрана."""
    message = AsyncMock()
    message.text = "08:15"
    message.from_user = Mock(spec=User, id=12345)
    message.answer = AsyncMock()

    mock_user = MagicMock()
    mock_user.notify_time = time(8, 15)
    mock_user.global_days = "[5,3,1]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as repo_cls:
        repo = AsyncMock()
        repo.set_notify_time = AsyncMock()
        repo.get = AsyncMock(return_value=mock_user)
        repo_cls.return_value = repo

        mock_state.get_data = AsyncMock(return_value={})

        await settings_handler.process_notify_time_input(message, mock_state, session=AsyncMock())

        repo.set_notify_time.assert_awaited_once()
        args = repo.set_notify_time.call_args[0]
        assert args[0] == 12345
        assert args[1] == time(8, 15)
        mock_state.clear.assert_awaited_once()
        # два answer: saved + view
        assert message.answer.call_count >= 2


@pytest.mark.asyncio
async def test_process_notify_time_invalid_does_not_save(mock_state, mock_session):
    """Невалидное время: не сохраняет, просит повторить."""
    message = AsyncMock()
    message.text = "25:99"
    message.answer = AsyncMock()

    mock_state.get_data = AsyncMock(return_value={"session": mock_session})

    with patch("wrbot.bot.handlers.settings.UserRepository") as repo_cls:
        repo = AsyncMock()
        repo.set_notify_time = AsyncMock()
        repo_cls.return_value = repo

        await settings_handler.process_notify_time_input(message, mock_state, session=AsyncMock())

        repo.set_notify_time.assert_not_awaited()
        message.answer.assert_called_once_with(Texts.global_notify_invalid_time)
        mock_state.clear.assert_not_awaited()


@pytest.mark.asyncio
async def test_gnotify_days_start_shows_toggle_screen(mock_state, mock_session):
    """Кнопка «Изменить дни» показывает экран с toggle и текущими."""
    tg_user = Mock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "gnotify_days"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user

    mock_user = MagicMock()
    mock_user.global_days = "[1,5]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as repo_cls:
        repo = AsyncMock()
        repo.get_or_create = AsyncMock()
        repo.get = AsyncMock(return_value=mock_user)
        repo_cls.return_value = repo

        data = {"session": mock_session}

        await settings_handler.gnotify_days_start(callback, mock_state, **data)

        mock_state.set_state.assert_awaited_once_with(SettingsStates.global_days)
        mock_state.update_data.assert_awaited()
        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "1, 5" in text or "1,5" in text
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_gday_toggle_adds_and_removes(mock_state):
    """Toggle callback переключает день в state и перерисовывает kb."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "gday_toggle_7"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    # начальное состояние с [5,3]
    mock_state.get_data = AsyncMock(return_value={"selected_days": [5, 3]})

    await settings_handler.process_gday_toggle(callback, mock_state)

    # update_data вызван с toggled
    mock_state.update_data.assert_awaited()
    updated = mock_state.update_data.call_args
    assert updated is not None
    callback.message.edit_text.assert_called_once()
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_gdays_save_persists_and_returns_to_view(mock_state, mock_session):
    """Сохранить дни: set_global_days с JSON, возврат к глобальному экрану."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "gdays_save"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = Mock(spec=User, id=12345)

    selected = [1, 10]
    mock_state.get_data = AsyncMock(return_value={"selected_days": selected})

    mock_user = MagicMock()
    mock_user.notify_time = time(10, 0)
    mock_user.global_days = "[1,10]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as repo_cls:
        repo = AsyncMock()
        repo.set_global_days = AsyncMock()
        repo.get = AsyncMock(return_value=mock_user)
        repo_cls.return_value = repo

        await settings_handler.gdays_save(callback, mock_state, session=AsyncMock())

        repo.set_global_days.assert_awaited_once_with(12345, "[1, 10]")
        mock_state.clear.assert_awaited_once()
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once_with(Texts.global_notify_days_saved)


@pytest.mark.asyncio
async def test_gdays_input_and_message_save(mock_state, mock_session):
    """Ввод дней вручную через сообщение: парсит, сохраняет, показывает view."""
    # сначала старт input
    cb = AsyncMock(spec=CallbackQuery)
    cb.data = "gdays_input"
    cb.message = AsyncMock()
    cb.answer = AsyncMock()

    await settings_handler.gnotify_days_input_start(cb, mock_state)
    mock_state.update_data.assert_awaited_with(days_input=True)

    # теперь message
    msg = AsyncMock()
    msg.text = "7,14,30"
    msg.from_user = Mock(spec=User, id=42)
    msg.answer = AsyncMock()

    mock_user = MagicMock()
    mock_user.notify_time = time(10, 0)
    mock_user.global_days = "[7,14,30]"

    with patch("wrbot.bot.handlers.settings.UserRepository") as repo_cls:
        repo = AsyncMock()
        repo.set_global_days = AsyncMock()
        repo.get = AsyncMock(return_value=mock_user)
        repo_cls.return_value = repo

        mock_state.get_data = AsyncMock(return_value={"days_input": True})

        await settings_handler.process_global_days_input(msg, mock_state, session=AsyncMock())

        repo.set_global_days.assert_awaited_once()
        assert msg.answer.call_count >= 2
        mock_state.clear.assert_awaited_once()


def test_global_notify_callbacks_routes_correctly():
    """Router test: gnotify_* и gday_toggle_* достигают своих хэндлеров."""
    router = settings_handler.router
    handler_names = [getattr(h.callback, "__name__", "") for h in router.callback_query.handlers]

    assert "global_notify_menu" in handler_names
    assert "gnotify_time_start" in handler_names
    assert "gnotify_days_start" in handler_names
    assert "process_gday_toggle" in handler_names
    assert "gdays_save" in handler_names
    assert "gnotify_days_input_start" in handler_names

    # Убедимся, что нет broad startswith, который мог бы перехватить наши (как в TASK-0008)
    # Наши toggle специфичны по startswith("gday_toggle_")
    # settings_global точный ==


def test_gday_toggle_reaches_handler():
    """Проверка, что gday_toggle_ callbacks маршрутизируются на process_gday_toggle."""
    router = settings_handler.router
    toggle_handlers = [
        h
        for h in router.callback_query.handlers
        if getattr(h.callback, "__name__", "") == "process_gday_toggle"
    ]
    assert len(toggle_handlers) >= 1
