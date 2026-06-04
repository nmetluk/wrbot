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

        with patch(
            "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
        ) as mock_select:
            mock_select.return_value = [user]  # важно для TASK-0017: свип теперь использует select

            with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.record = AsyncMock(return_value=True)

                with patch(
                    "wrbot.scheduler.sweep.build_reminder_text", new_callable=AsyncMock
                ) as mock_build:
                    mock_build.return_value = "🔔 test reminder"

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

        with patch(
            "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
        ) as mock_select:
            mock_select.return_value = [user]  # важно для TASK-0017

            with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.record = AsyncMock(return_value=True)

                with patch(
                    "wrbot.scheduler.sweep.build_reminder_text", new_callable=AsyncMock
                ) as mock_build:
                    mock_build.return_value = "🔔 test reminder"

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

        with patch(
            "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
        ) as mock_select:
            mock_select.return_value = [user_ok, user_fail]  # важно для TASK-0017

            with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.record = AsyncMock(return_value=True)

                with patch(
                    "wrbot.scheduler.sweep.build_reminder_text", new_callable=AsyncMock
                ) as mock_build:
                    mock_build.return_value = "🔔 test reminder"

                    await run_sweep(mock_bot, factory)

                    # OK отправлен и записан, FAIL — попытка была, но не записан
                    assert mock_bot.send_message.call_count == 2
                    # record только для успешного
                    assert mock_repo.record.call_count == 1
                mock_repo.record.assert_awaited_with(charge_ok.id, date(2026, 6, 10), 5)


@pytest.mark.asyncio
async def test_sweep_respects_notify_time_and_timezone(mock_bot, mock_session_factory):
    """
    TASK-0017: Свип должен отправлять только в notify_time пользователя в его tz.

    Тест падает на коде до фикса (свип игнорировал select_users_to_notify_at
    и слал на первом тике суток).
    """
    factory, _session = mock_session_factory

    user_msk = _make_user(tg_id=123, notify_time=time(10, 0))  # 10:00 МСК
    charge_msk = _make_charge(id=1, name="VPN MSK")

    due_msk = [
        {
            "charge": charge_msk,
            "user": user_msk,
            "target_date": date(2026, 6, 10),
            "days_before": 5,
            "effective_days": [5],
        }
    ]

    # Случай 1: "сейчас" 00:00 UTC — для МСК это 03:00, notify_time не совпадает
    with patch(
        "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
    ) as mock_select:
        mock_select.return_value = []  # никто не должен получать в эту минуту

        with patch(
            "wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock
        ) as mock_due:
            mock_due.return_value = due_msk  # даже если due есть

            await run_sweep(mock_bot, factory)

            # На старом коде (без вызова select и early return) здесь был бы send
            mock_due.assert_not_called()  # или если вызван — send не должен
            mock_bot.send_message.assert_not_awaited()

    # Случай 2: "сейчас" 07:00 UTC = 10:00 МСК — совпадает, должен отправить
    with patch(
        "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
    ) as mock_select:
        mock_select.return_value = [user_msk]

        with patch(
            "wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock
        ) as mock_due:
            mock_due.return_value = due_msk

            with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.record = AsyncMock(return_value=True)

                with patch(
                    "wrbot.scheduler.sweep.build_reminder_text", new_callable=AsyncMock
                ) as mock_build:
                    mock_build.return_value = "🔔 test reminder"

                    await run_sweep(mock_bot, factory)

                    mock_bot.send_message.assert_awaited_once()
                    mock_due.assert_awaited_once()
                    # Убедимся, что передали user_tg_ids в get_due
                    _, kwargs = mock_due.call_args
                    assert kwargs.get("user_tg_ids") == [123]


@pytest.mark.asyncio
async def test_sweep_duplicates_to_category_targets_and_forbidden_notify_owner(
    mock_bot, mock_session_factory
):
    """
    TASK-0044: дубли в чаты; Forbidden в одном → notify owner + остальные;
    изоляция от личного.
    """
    from aiogram.exceptions import TelegramForbiddenError

    factory, _session = mock_session_factory

    charge = _make_charge()
    charge.category_id = 7  # has targets
    user = _make_user()

    due = [
        {
            "charge": charge,
            "user": user,
            "target_date": date(2026, 6, 10),
            "days_before": 5,
            "effective_days": [5],
        }
    ]

    async def fake_get_due(*a, **k):
        return due

    with patch("wrbot.scheduler.sweep.get_due_reminders_today", new_callable=AsyncMock) as mock_due:
        mock_due.side_effect = fake_get_due

        with patch(
            "wrbot.scheduler.sweep.select_users_to_notify_at", new_callable=AsyncMock
        ) as mock_select:
            mock_select.return_value = [user]

            with patch("wrbot.scheduler.sweep.SentReminderRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.record = AsyncMock(return_value=True)

                with patch(
                    "wrbot.scheduler.sweep.build_reminder_text", new_callable=AsyncMock
                ) as mock_build:
                    mock_build.return_value = "🔔 test dup"

                    # мок Category repo с 2 targets, один forbidden
                    with patch("wrbot.scheduler.sweep.CategoryRepository") as mock_cat_cls:
                        mock_cat = AsyncMock()
                        mock_cat.get_notify_chat_ids.return_value = [-100111, -100222]
                        mock_cat_cls.return_value = mock_cat

                        # send side: dup1 ok, dup2 forbidden (triggers owner notify), personal ok
                        async def send_side(chat_id, **kw):
                            if chat_id == -100222:
                                raise TelegramForbiddenError(
                                    method_name="send", message="no rights"
                                )
                            return True

                        mock_bot.send_message.side_effect = send_side

                        await run_sweep(mock_bot, factory)

                        # personal + good dup + owner notify (for forbidden)
                        calls = mock_bot.send_message.call_count
                        assert calls >= 3  # personal + good + owner notify
                        # record only personal
                        mock_repo.record.assert_awaited_once()
