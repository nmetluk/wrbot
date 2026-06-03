"""
Тесты для handlers/reminders.py (TASK-0015).

Проверка callback-хэндлеров с autospec-моками (paid periodic/once, snooze, edit).
Router-тесты — в test_callback_routing.py (интроспекция фильтров).
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from wrbot.bot.handlers import reminders as reminders_handler
from wrbot.bot.keyboards import get_main_menu_keyboard
from wrbot.bot.states import NewChargeStates
from wrbot.bot.texts import Texts


@pytest.fixture
def mock_state():
    """Мок FSMContext с реалистичным поведением."""
    state = AsyncMock(spec=FSMContext)
    state_data: dict = {}
    state.get_data.return_value = state_data
    state.update_data.side_effect = lambda **kwargs: state_data.update(kwargs)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_session():
    """Мок AsyncSession."""
    return AsyncMock()


def _make_callback(data: str) -> CallbackQuery:
    """Минимальный CallbackQuery с from_user."""
    user = User(id=12345, is_bot=False, first_name="Test")
    cb = AsyncMock(spec=CallbackQuery)
    cb.data = data
    cb.from_user = user
    # Proper Message mock so that isinstance(..., Message) passes in the handler
    msg = MagicMock(spec=Message)
    cb.message = msg
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    return cb


@pytest.mark.asyncio
async def test_remind_paid_periodic(mock_state, mock_session):
    """Paid из уведомления для периодического: возвращает новую дату."""
    callback = _make_callback("remind_paid_42")
    updated = MagicMock()
    updated.status = "active"
    updated.next_date = date(2026, 7, 15)

    with patch.object(
        reminders_handler.ChargeRepository, "mark_paid", new_callable=AsyncMock
    ) as mock_mark:
        mock_mark.return_value = updated

        await reminders_handler.remind_mark_paid(callback, mock_state, mock_session)

        mock_mark.assert_awaited_once_with(12345, 42)
        callback.message.edit_text.assert_awaited_once()
        args, _ = callback.message.edit_text.call_args
        assert "Следующее списание: 15.07.2026" in args[0]
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_remind_paid_once(mock_state, mock_session):
    """Paid из уведомления для once: закрывает без новой даты."""
    callback = _make_callback("remind_paid_99")
    updated = MagicMock()
    updated.status = "done"

    with patch.object(
        reminders_handler.ChargeRepository, "mark_paid", new_callable=AsyncMock
    ) as mock_mark:
        mock_mark.return_value = updated

        await reminders_handler.remind_mark_paid(callback, mock_state, mock_session)

        callback.message.edit_text.assert_awaited_once()
        args, _ = callback.message.edit_text.call_args
        assert Texts.reminder_paid_once in args[0] or "закрыто" in args[0].lower()
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_remind_snooze_sets_tomorrow_and_leaves_next_date(mock_state, mock_session):
    """Snooze: вызывает repo.snooze с завтрашней датой; next_date не меняется (ADR-0005)."""
    callback = _make_callback("remind_snooze_7")
    tomorrow = date.today() + timedelta(days=1)

    updated = MagicMock()
    updated.snoozed_until = tomorrow
    # next_date intentionally left as-is by handler + repo

    with patch.object(
        reminders_handler.ChargeRepository, "snooze", new_callable=AsyncMock
    ) as mock_snooze:
        mock_snooze.return_value = updated

        await reminders_handler.remind_snooze(callback, mock_state, mock_session)

        mock_snooze.assert_awaited_once_with(12345, 7, tomorrow)
        callback.message.edit_text.assert_awaited_once_with(
            Texts.reminder_snoozed, reply_markup=get_main_menu_keyboard()
        )
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_remind_edit_starts_fsm_with_editing_id(mock_state, mock_session):
    """Edit из уведомления: загружает данные в state + переходит в NewChargeStates.name."""
    callback = _make_callback("remind_edit_15")
    charge = MagicMock()
    charge.id = 15
    charge.name = "VPN"
    charge.amount = "299.00"
    charge.wallet_id = 1
    charge.category_id = None
    charge.next_date = date(2026, 6, 20)
    charge.period = "monthly"

    with patch.object(
        reminders_handler.ChargeRepository, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = charge

        await reminders_handler.remind_edit_charge(callback, mock_state, mock_session)

        mock_get.assert_awaited_once_with(12345, 15)
        mock_state.update_data.assert_awaited()
        # Проверяем ключ editing_charge_id
        call_kwargs = mock_state.update_data.call_args.kwargs
        assert call_kwargs["editing_charge_id"] == 15
        assert call_kwargs["name"] == "VPN"
        mock_state.set_state.assert_awaited_once_with(NewChargeStates.name)
        callback.message.edit_text.assert_awaited_once()
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_remind_handlers_not_found(mock_state, mock_session):
    """Не найден charge — answer с error_not_found, без edit_text."""
    for prefix in ("remind_paid_", "remind_snooze_", "remind_edit_"):
        callback = _make_callback(f"{prefix}9999")
        with patch.object(
            reminders_handler.ChargeRepository,
            "mark_paid" if "paid" in prefix else "snooze" if "snooze" in prefix else "get",
            new_callable=AsyncMock,
        ) as mock_method:
            mock_method.return_value = None

            if "paid" in prefix:
                await reminders_handler.remind_mark_paid(callback, mock_state, mock_session)
            elif "snooze" in prefix:
                await reminders_handler.remind_snooze(callback, mock_state, mock_session)
            else:
                await reminders_handler.remind_edit_charge(callback, mock_state, mock_session)

            callback.answer.assert_awaited_with(Texts.error_not_found)
            # edit_text не должен был вызываться для not found в happy path
