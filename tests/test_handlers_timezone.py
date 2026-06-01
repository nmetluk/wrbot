"""
Тесты для TZ handlers (TASK-0025).

Включая router test на маршрутизацию специфичных callback'ов.
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from wrbot.bot.handlers import settings as settings_handler


@pytest.fixture
def mock_state():
    state = AsyncMock(spec=FSMContext)
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_settings_tz_menu_callback():
    """Callback settings_tz показывает меню TZ."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "settings_tz"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = AsyncMock(id=12345)

    with patch("wrbot.bot.handlers.settings.UserRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo.get_or_create = AsyncMock()
        mock_repo.get = AsyncMock(return_value=AsyncMock(tz="Europe/Moscow"))
        mock_repo_cls.return_value = mock_repo

        await settings_handler.tz_menu(callback, session=AsyncMock())

        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_tz_set_callback_valid():
    """tz_set_... с валидным TZ сохраняет и показывает успех."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "tz_set_Europe_Moscow"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = AsyncMock(id=12345)

    with patch("wrbot.bot.handlers.settings.UserRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo.set_tz = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        await settings_handler.process_tz_choice(callback, session=AsyncMock())

        mock_repo.set_tz.assert_awaited_once_with(12345, "Europe/Moscow")
        callback.answer.assert_called_once()


def test_tz_callbacks_routes_correctly():
    """Router test: tz_set_ callbacks reach process_tz_choice."""
    router = settings_handler.router
    names = [getattr(h.callback, "__name__", "") for h in router.callback_query.handlers]
    assert "process_tz_choice" in names
    # settings_tz too
    assert "tz_menu" in names
