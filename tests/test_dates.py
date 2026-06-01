"""
Tests for date/period calculation (TASK-0010).

Covers edge cases required by the task: end-of-month clamp, leap years,
quarter/year boundaries.
"""

from datetime import date

import pytest

from wrbot.services.dates import calculate_next_date


@pytest.mark.parametrize(
    "current,period,expected",
    [
        # Monthly clamp
        (date(2026, 1, 31), "monthly", date(2026, 2, 28)),
        (date(2026, 3, 31), "monthly", date(2026, 4, 30)),
        (date(2026, 5, 31), "monthly", date(2026, 6, 30)),
        (date(2026, 8, 31), "monthly", date(2026, 9, 30)),
        # Leap year February
        (date(2024, 1, 31), "monthly", date(2024, 2, 29)),
        (date(2024, 1, 31), "quarterly", date(2024, 4, 30)),
        # Quarterly
        (date(2026, 1, 31), "quarterly", date(2026, 4, 30)),
        (date(2026, 10, 31), "quarterly", date(2027, 1, 31)),
        # Yearly
        (date(2026, 1, 31), "yearly", date(2027, 1, 31)),
        (date(2026, 2, 28), "yearly", date(2027, 2, 28)),
        # Once — no shift
        (date(2026, 1, 15), "once", date(2026, 1, 15)),
        (date(2026, 12, 31), "once", date(2026, 12, 31)),
    ],
)
def test_calculate_next_date(current: date, period: str, expected: date) -> None:
    result = calculate_next_date(current, period)  # type: ignore[arg-type]
    assert result == expected


def test_calculate_next_date_invalid_period_fallback() -> None:
    """Unknown period falls back to returning current (defensive)."""
    d = date(2026, 5, 15)
    # The Literal type prevents this at runtime in normal use, but we test the fallback
    result = calculate_next_date(d, "invalid")  # type: ignore[arg-type]
    assert result == d
