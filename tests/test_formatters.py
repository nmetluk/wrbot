"""
Unit tests for formatters (TASK-0039).

Covers pure functions + real Texts render (anti-drift: no mock of t()/Texts).
Async resolver + build helpers covered via e2e (dp.feed_update in test_e2e_smoke).
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wrbot.bot.texts import Texts
from wrbot.services.formatters import (
    build_reminder_text,
    format_charge_button_text,
    format_date_ru,
    format_notify_for_charge,
    format_notify_from_fsm,
    format_period_ru,
)


@pytest.mark.parametrize(
    "inp,expected",
    [
        (date(2026, 6, 3), "03.06.2026"),
        ("2026-12-31", "31.12.2026"),
        (None, "?"),
        ("not-a-date", "not-a-date"),
    ],
)
def test_format_date_ru(inp, expected: str) -> None:
    assert format_date_ru(inp) == expected


@pytest.mark.parametrize(
    "period,expected",
    [
        ("once", "одноразово"),
        ("monthly", "ежемесячно"),
        ("quarterly", "ежеквартально"),
        ("yearly", "ежегодно"),
        (None, "?"),
        ("unknown", "unknown"),
    ],
)
def test_format_period_ru(period: str | None, expected: str) -> None:
    assert format_period_ru(period) == expected


def test_format_notify_from_fsm() -> None:
    assert format_notify_from_fsm(None) == Texts.notify_global
    assert format_notify_from_fsm({"type": "global"}) == Texts.notify_global
    assert format_notify_from_fsm({"type": "disabled"}) == Texts.notify_disabled
    assert format_notify_from_fsm({"disabled": True}) == Texts.notify_disabled
    assert format_notify_from_fsm(
        {"type": "custom", "days": [1, 15, 5]}
    ) == Texts.notify_custom.format(days="1, 15, 5")


class _FakeCharge:
    def __init__(self, ind_days: str | None) -> None:
        self.individual_days = ind_days


def test_format_notify_for_charge() -> None:
    assert format_notify_for_charge(_FakeCharge(None)) == Texts.notify_global
    assert format_notify_for_charge(_FakeCharge("[]")) == Texts.notify_disabled
    assert format_notify_for_charge(_FakeCharge('[1, "3", 10]')) == Texts.notify_custom.format(
        days="1, 3, 10"
    )
    assert format_notify_for_charge(_FakeCharge("not json")) == Texts.notify_global


def test_format_charge_button_text_real_template() -> None:
    """Реальный рендер через Texts (анти-дрейф, без мока)."""
    result = format_charge_button_text(
        name="Тест", amount="42.00 ₽", wallet="Кошелёк", next_date="05.05.2026"
    )
    assert result == "Тест — 42.00 ₽ (Кошелёк) — 05.05.2026"
    # Убеждаемся, что шаблон из Texts использован (содержит паттерн)
    assert (
        Texts.my_charges_button.format(
            name="Тест", amount="42.00 ₽", wallet="Кошелёк", next_date="05.05.2026"
        )
        == result
    )


@pytest.mark.asyncio
async def test_build_reminder_text_real_template() -> None:
    """Реальный рендер reminder_notification через Texts + форматтеры (TASK-0039 анти-дрейф)."""
    mock_session = AsyncMock()
    fake_charge = MagicMock()
    fake_charge.wallet_id = 7
    fake_charge.name = "Оплата VPN"
    fake_charge.amount = Decimal("299.00")
    fake_charge.currency = "RUB"
    fake_charge.next_date = "2026-07-15"  # formatter handles iso str

    with patch("wrbot.services.formatters.resolve_wallet_name", new_callable=AsyncMock) as mock_res:
        mock_res.return_value = "Сбер"
        with patch("wrbot.services.formatters.format_date_ru", return_value="15.07.2026"):
            result = await build_reminder_text(mock_session, 12345, fake_charge)

    assert "🔔 *Напоминание о списании*" in result
    assert "Оплата VPN" in result
    assert "299.00 ₽" in result
    assert "Сбер" in result
    assert "15.07.2026" in result

    # verify used the Texts template (real, no mock of t())
    expected = Texts.reminder_notification.format(
        name="Оплата VPN", amount="299.00 ₽", wallet="Сбер", next_date="15.07.2026"
    )
    assert result == expected
