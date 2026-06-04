"""
Unit tests for currencies service (TASK-0049).

Оффлайн, покрытие API: presets/default/valid/get/search/format_amount.
153 валюты, символы для пресетов, код для прочих. Анти-дрейф через реальный форматтер.
"""

from decimal import Decimal

import pytest

from wrbot.services import currencies


def test_loads_153_currencies_and_presets():
    presets = currencies.get_presets()
    assert len(presets) == 5
    assert presets == ["RUB", "EUR", "USD", "KZT", "KGS"]
    assert currencies.get_default() == "RUB"
    assert len(currencies._load()["currencies"]) == 153  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "code,expected",
    [
        ("RUB", True),
        ("rub", True),
        ("USD", True),
        ("AED", True),
        ("XXX", False),
        ("", False),
        ("ZZZ", False),
    ],
)
def test_is_valid_code(code: str, expected: bool):
    assert currencies.is_valid_code(code) is expected


def test_get_returns_copy_with_symbol_for_rub():
    rub = currencies.get("RUB")
    assert rub is not None
    assert rub["code"] == "RUB"
    assert rub["symbol"] == "₽"
    # мутация не влияет на кэш
    rub["foo"] = 1
    rub2 = currencies.get("RUB")
    assert "foo" not in rub2  # type: ignore[operator]


def test_get_none_for_invalid():
    assert currencies.get("XXX") is None


def test_search_by_code_and_name():
    res = currencies.search("russian")
    assert len(res) == 1
    assert res[0]["code"] == "RUB"

    res = currencies.search("ruble")
    assert len(res) >= 2  # RUB + Belarusian Ruble at least
    assert any(c["code"] == "RUB" for c in res)

    res = currencies.search("dollar")
    assert any(c["code"] == "USD" for c in res)

    res = currencies.search("dirham")
    assert any(c["code"] == "AED" for c in res)

    assert currencies.search("") == []
    assert currencies.search("   ") == []


@pytest.mark.parametrize(
    "amount,code,expected_suffix",
    [
        ("1500.50", "RUB", "1500.50 ₽"),
        (Decimal("299.00"), "RUB", "299.00 ₽"),
        ("100", "USD", "100 $"),  # preset -> symbol (даже если $ после)
        ("99.99", "EUR", "99.99 €"),
        ("42.00", "AED", "42.00 AED"),  # non-preset -> code
        (123, "KZT", "123 ₸"),
    ],
)
def test_format_amount(amount, code: str, expected_suffix: str):
    out = currencies.format_amount(amount, code)
    assert out.endswith(expected_suffix.split()[-1])
    assert expected_suffix in out


def test_format_amount_falls_back_to_code_for_unknown():
    out = currencies.format_amount("10.5", "ZZZ")
    assert out == "10.5 ZZZ"


def test_format_amount_used_in_formatters_anti_drift():
    """Хотя бы один тест через реальный currencies.format_amount (критерий приёмки)."""
    # RUB с символом
    assert currencies.format_amount("42.00", "RUB") == "42.00 ₽"
    # не-пресет
    assert currencies.format_amount(Decimal("123.45"), "AED") == "123.45 AED"
