"""
Charts rendering for M6 daily admin dashboard (TASK-0034, ADR-0008).

All charts use non-interactive Agg backend (no display, works in CI/Docker).
Return PNG as bytes (suitable for BufferedInputFile / send_photo / media_group).
"""

import io
import logging
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


def _fig_to_png(fig: Figure, dpi: int = 120) -> bytes:
    """Save fig to bytes PNG, close it, return bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def render_user_growth_chart(data: list[dict[str, Any]]) -> bytes:
    """Линия: накопительный рост пользователей за 30 дней."""
    fig, ax = plt.subplots(figsize=(8, 3.5))
    dates = [item["date"] for item in data]
    cum = [item["cumulative"] for item in data]
    ax.plot(dates, cum, marker="o", linewidth=1.5, markersize=3, color="#2E86AB")
    ax.set_title("Рост пользователей (накопительно, 30 дней)")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Всего пользователей")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return _fig_to_png(fig)


def render_daily_activity_chart(data: list[dict[str, Any]]) -> bytes:
    """Бары: новые и активные пользователи за день (последние N дней)."""
    fig, ax = plt.subplots(figsize=(8, 3.5))
    dates = [item["date"] for item in data]
    new_u = [item["new"] for item in data]
    active = [item["active"] for item in data]
    x = range(len(dates))
    width = 0.35
    ax.bar([i - width / 2 for i in x], new_u, width, label="Новые", color="#28A745")
    ax.bar([i + width / 2 for i in x], active, width, label="Активные (по audit)", color="#17A2B8")
    ax.set_title("Новые и активные пользователи по дням")
    ax.set_xticks(list(x))
    ax.set_xticklabels([d.strftime("%m-%d") for d in dates], rotation=45, ha="right")
    ax.set_ylabel("Количество")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    return _fig_to_png(fig)


def render_charges_created_chart(data: list[dict[str, Any]]) -> bytes:
    """Бар: создано списаний за день (14 дней)."""
    fig, ax = plt.subplots(figsize=(8, 3.2))
    dates = [item["date"] for item in data]
    counts = [item["count"] for item in data]
    ax.bar(dates, counts, color="#6C757D")
    ax.set_title("Создано списаний за день (14 дней)")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Количество")
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    return _fig_to_png(fig)


def render_payments_chart(data: list[dict[str, Any]]) -> bytes:
    """Бар: отмечено оплат (кол-во + сумма) за день."""
    fig, ax1 = plt.subplots(figsize=(8, 3.2))
    dates = [item["date"] for item in data]
    counts = [item["count"] for item in data]
    sums = [item["sum"] for item in data]
    x = range(len(dates))
    ax1.bar([i - 0.2 for i in x], counts, 0.4, label="Кол-во", color="#FD7E14")
    ax1.set_ylabel("Кол-во оплат")
    ax1.tick_params(axis="y")

    ax2 = ax1.twinx()
    ax2.bar([i + 0.2 for i in x], sums, 0.4, label="Сумма", color="#DC3545")
    ax2.set_ylabel("Сумма (руб)")

    ax1.set_title("Оплачено за день (кол-во + сумма)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([d.strftime("%m-%d") for d in dates], rotation=45, ha="right")
    fig.legend(loc="upper left", bbox_to_anchor=(0.15, 0.88))
    plt.tight_layout()
    return _fig_to_png(fig)


def render_period_pie(dist: dict[str, int]) -> bytes:
    """Pie: распределение активных списаний по периодам."""
    fig, ax = plt.subplots(figsize=(5, 5))
    labels = list(dist.keys())
    sizes = list(dist.values())
    if not sizes or sum(sizes) == 0:
        sizes = [1]
        labels = ["нет данных"]
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Распределение активных списаний по периодам")
    plt.tight_layout()
    return _fig_to_png(fig)


def render_top_categories_chart(data: list[dict[str, Any]]) -> bytes:
    """Horizontal bar: топ категорий по числу (или сумме) активных."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    if not data:
        data = [{"name": "нет данных", "count": 1}]
    names = [d["name"][:20] for d in data]
    counts = [d["count"] for d in data]
    y = range(len(names))
    ax.barh(y, counts, color="#20C997")
    ax.set_yticks(list(y))
    ax.set_yticklabels(names)
    ax.set_xlabel("Количество активных")
    ax.set_title("Топ категорий (по числу активных списаний)")
    ax.invert_yaxis()
    plt.tight_layout()
    return _fig_to_png(fig)


def render_reminders_chart(data: list[dict[str, Any]]) -> bytes:
    """Бар: отправлено напоминаний за день."""
    fig, ax = plt.subplots(figsize=(7, 3))
    dates = [item["date"] for item in data]
    counts = [item["count"] for item in data]
    ax.bar(dates, counts, color="#6610F2")
    ax.set_title("Отправлено напоминаний за день")
    ax.set_ylabel("Кол-во")
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    return _fig_to_png(fig)


def render_errors_chart(data: list[dict[str, Any]]) -> bytes:
    """Бар: критичные ошибки за день (из error-hook + audit)."""
    fig, ax = plt.subplots(figsize=(7, 3))
    dates = [item["date"] for item in data]
    counts = [item["count"] for item in data]
    ax.bar(dates, counts, color="#E83E8C")
    ax.set_title("Критичные ошибки за день (error-hook)")
    ax.set_ylabel("Кол-во")
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    return _fig_to_png(fig)
