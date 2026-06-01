"""
Тесты для свипа уведомлений (TASK-0016).

Проверяют:
- Выбор due + отправка
- Идемпотентность (2 прогона свипа → 1 вызов send_message)
- Обработка snooze / отсутствие due
- Изоляция ошибок (один пользователь падает — остальные шлются)
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot

from wrbot.scheduler.sweep import run_sweep


@pytest.fixture
def mock_bot() -> AsyncMock:
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_session_factory():
    """Фабрика, возвращающая мок сессии с нужными атрибутами."""
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False

    factory = MagicMock(return_value=session)
    return factory, session


def _make_charge(**overrides):
    ch = MagicMock()
    ch.id = overrides.get("id", 42)
    ch.name = overrides.get("name", "VPN")
    ch.amount = overrides.get("amount", Decimal("299.00"))
    ch.wallet_id = overrides.get("wallet_id", 1)
    ch.next_date = overrides.get("next_date", date(2026, 6, 15))
    ch.status = "active"
    ch.snoozed_until = overrides.get("snoozed_until")
    return ch


def _make_user(**overrides):
    u = MagicMock()
    u.tg_id = overrides.get("tg_id", 12345)
    u.notify_time = overrides.get("notify_time", time(10, 0))
    u.tz = overrides.get("tz", "Europe/Moscow")
    return u


@pytest.mark.asyncio
async def test_sweep_sends_and_records(mock_bot, mock_session_factory):
    factory, _session = mock_session_factory

    charge = _make_charge()
    user = _make_user()

    due = [
        {
            "charge": charge,
            "user": user,
            "target_date": date(2026, 6, 10),
            "days_before": 5,
            "effective_days": [5, 3, 1],
        }
    ]

    with patch("wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock) as mock_due:
        mock_due.return_value = due

        with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.record = AsyncMock(return_value=True)

            await run_sweep(mock_bot, factory)

            mock_bot.send_message.assert_awaited_once()
            mock_repo.record.assert_awaited_once_with(charge.id, date(2026, 6, 10), 5)


@pytest.mark.asyncio
async def test_sweep_idempotent_two_ticks_one_send(mock_bot, mock_session_factory):
    """Два прогона свипа в один день для одного due → только одна отправка
    (благодаря was_sent внутри get_due).
    """
    factory, _session = mock_session_factory

    charge = _make_charge()
    user = _make_user()

    due = [
        {
            "charge": charge,
            "user": user,
            "target_date": date(2026, 6, 10),
            "days_before": 5,
            "effective_days": [5, 3, 1],
        }
    ]

    with patch("wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock) as mock_due:
        # Первый тик возвращает due, второй — пусто
        # (симулируем, что was_sent уже true после первой записи)
        mock_due.side_effect = [due, []]

        with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.record = AsyncMock(return_value=True)

            await run_sweep(mock_bot, factory)
            await run_sweep(mock_bot, factory)

            assert mock_bot.send_message.call_count == 1
            assert mock_repo.record.call_count == 1


@pytest.mark.asyncio
async def test_sweep_no_due_nothing_sent(mock_bot, mock_session_factory):
    factory, _session = mock_session_factory

    with patch("wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock) as mock_due:
        mock_due.return_value = []

        await run_sweep(mock_bot, factory)

        mock_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_sweep_error_isolation_one_user_fails_others_succeed(mock_bot, mock_session_factory):
    factory, _session = mock_session_factory

    charge_ok = _make_charge(id=1, name="OK")
    user_ok = _make_user(tg_id=111)
    charge_fail = _make_charge(id=2, name="FAIL")
    user_fail = _make_user(tg_id=222)

    due = [
        {
            "charge": charge_ok,
            "user": user_ok,
            "target_date": date(2026, 6, 10),
            "days_before": 5,
            "effective_days": [5],
        },
        {
            "charge": charge_fail,
            "user": user_fail,
            "target_date": date(2026, 6, 10),
            "days_before": 3,
            "effective_days": [5, 3],
        },
    ]

    async def send_side_effect(*, chat_id, **kwargs):
        if chat_id == 222:
            raise RuntimeError("Telegram down for this user")
        return MagicMock()

    mock_bot.send_message.side_effect = send_side_effect

    with patch("wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock) as mock_due:
        mock_due.return_value = due

        with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.record = AsyncMock(return_value=True)

            await run_sweep(mock_bot, factory)

            # OK отправлен и записан, FAIL — попытка была, но не записан
            assert mock_bot.send_message.call_count == 2
            # record только для успешного
            assert mock_repo.record.call_count == 1
            mock_repo.record.assert_awaited_with(charge_ok.id, date(2026, 6, 10), 5)
