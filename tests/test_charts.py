"""
Smoke tests for charts rendering (TASK-0034).

- Все render_* возвращают bytes, начинающиеся с PNG сигнатуры.
- Размер > 0 (реально нарисовали).
- Не падают на пустых данных.
- Используют Agg (не требуют дисплея).
"""

from datetime import date

from wrbot.services.charts import (
    render_charges_created_chart,
    render_daily_activity_chart,
    render_errors_chart,
    render_payments_chart,
    render_period_pie,
    render_reminders_chart,
    render_top_categories_chart,
    render_user_growth_chart,
)

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _assert_png(b: bytes) -> None:
    assert b.startswith(PNG_SIG), "not a PNG"
    assert len(b) > 200, "too small, probably empty plot"


def test_user_growth_renders_png():
    data = [
        {"date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i), "cumulative": 10 + i}
        for i in range(30)
    ]
    b = render_user_growth_chart(data)
    _assert_png(b)


def test_daily_activity_renders_png():
    data = [
        {
            "date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i),
            "new": i % 3,
            "active": 5 + i % 4,
        }
        for i in range(7)
    ]
    b = render_daily_activity_chart(data)
    _assert_png(b)


def test_charges_created_renders_png():
    data = [
        {"date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i), "count": (i % 5) + 1}
        for i in range(14)
    ]
    b = render_charges_created_chart(data)
    _assert_png(b)


def test_payments_renders_png():
    data = [
        {
            "date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i),
            "count": i % 4,
            "sum": float(100 * i),
        }
        for i in range(7)
    ]
    b = render_payments_chart(data)
    _assert_png(b)


def test_period_pie_renders_png():
    dist = {"monthly": 12, "quarterly": 3, "yearly": 1, "once": 2}
    b = render_period_pie(dist)
    _assert_png(b)


def test_top_categories_renders_png():
    data = [{"name": f"Cat{i}", "count": 10 - i, "total": 100.0} for i in range(5)]
    b = render_top_categories_chart(data)
    _assert_png(b)


def test_reminders_renders_png():
    data = [
        {"date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i), "count": i % 5}
        for i in range(7)
    ]
    b = render_reminders_chart(data)
    _assert_png(b)


def test_errors_renders_png():
    data = [
        {"date": date(2026, 6, 1) + __import__("datetime").timedelta(days=i), "count": (i + 1) % 3}
        for i in range(7)
    ]
    b = render_errors_chart(data)
    _assert_png(b)


def test_charts_handle_empty_data():
    """Не падают на пустых/нулевых данных — рисуют плейсхолдеры."""
    b = render_period_pie({})
    _assert_png(b)
    b = render_top_categories_chart([])
    _assert_png(b)
