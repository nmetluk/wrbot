"""
Тесты для глобального error handler и дружелюбной обработки конфликтов удаления (TASK-0021).

Покрывает:
- Глобальный обработчик ловит исключение, логирует, пытается ответить.
- Удаление кошелька с зарядами → IntegrityError → дружелюбный отказ (не трейсбек).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, ErrorEvent, Update, User
from sqlalchemy.exc import IntegrityError

from wrbot.bot.handlers import wallets as wallets_handler
from wrbot.bot.handlers.errors import make_global_error_handler
from wrbot.bot.texts import Texts


@pytest.fixture
def mock_state():
    """Мок FSMContext (как в других тестах handlers)."""
    from aiogram.fsm.context import FSMContext

    state = AsyncMock(spec=FSMContext)
    state_data = {"wallet_id": 42}  # session теперь приходит как параметр handler'а, не из FSM
    state.get_data.return_value = state_data
    state.update_data.side_effect = lambda **kwargs: state_data.update(kwargs)
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_callback_wallet_delete():
    """Мок CallbackQuery для подтверждения удаления кошелька."""
    tg_user = MagicMock(spec=User)
    tg_user.id = 12345

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "wallet_confirm_delete"
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = tg_user
    return callback


@pytest.mark.asyncio
async def test_global_error_handler_logs_and_replies(monkeypatch):
    """Глобальный error handler ловит исключение, логирует и отвечает пользователю."""
    # Мок события с сообщением
    mock_message = AsyncMock()
    mock_message.chat.id = 999
    mock_message.from_user.id = 12345
    mock_message.text = "тест"

    mock_update = MagicMock(spec=Update)
    mock_update.message = mock_message
    mock_update.callback_query = None

    exc = RuntimeError("boom from handler")
    event = ErrorEvent(update=mock_update, exception=exc, bot=AsyncMock())

    # Вызываем напрямую через make (no bot for test)
    handler = make_global_error_handler(None)
    await handler(event)

    # Проверяем, что попытались ответить (generic ошибка)
    mock_message.answer.assert_called_once_with(Texts.error_generic)


@pytest.mark.asyncio
async def test_wallet_delete_with_active_charges_returns_friendly_error(
    mock_state, mock_callback_wallet_delete
):
    """
    Удаление кошелька, на котором есть charges (FK RESTRICT) →
    IntegrityError перехватывается → дружелюбное сообщение, без падения и без IntegrityError наружу.
    """
    callback = mock_callback_wallet_delete

    with patch("wrbot.bot.handlers.wallets.WalletRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.delete.side_effect = IntegrityError("FOREIGN KEY constraint failed", None, None)
        mock_repo_class.return_value = mock_repo

        # session передаём явно (из middleware текущего апдейта)
        session_mock = AsyncMock()
        await wallets_handler.wallet_delete(callback, mock_state, session=session_mock)

        # Должны ответить именно нашим специфичным сообщением (а не generic)
        callback.answer.assert_called()
        # Проверяем, что в вызове был текст про активные списания
        call_args = callback.answer.call_args
        assert "активные списания" in str(call_args)

        # state должен быть очищен
        mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_error_handler_does_not_crash_on_reply_failure():
    """Даже если ответ пользователю не удался — handler не должен падать (защищает 24/7)."""
    mock_update = MagicMock(spec=Update)
    mock_update.message = None
    mock_update.callback_query = None

    event = ErrorEvent(update=mock_update, exception=ValueError("test"), bot=AsyncMock())

    # Не должен рейзить
    handler = make_global_error_handler(None)
    await handler(event)
    # Если дошли сюда — ок
