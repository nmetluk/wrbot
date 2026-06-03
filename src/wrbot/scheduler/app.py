"""
APScheduler integration (M4, TASK-0016).

Планировщик для своевременной отправки напоминаний (NFR-1, NFR-2).
- UTC время, 1-минутный тик.
- In-memory jobstore (истина в БД + sent_reminders).
- Регистрация свипа после создания бота.
"""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Глобальный планировщик (инициализируется в __main__.py)
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    """Получить экземпляр планировщика."""
    return scheduler


def setup_scheduler() -> AsyncIOScheduler:
    """Создать и настроить AsyncIOScheduler (UTC, in-memory jobstore)."""
    global scheduler
    scheduler = AsyncIOScheduler(timezone=UTC)
    return scheduler


def register_sweep_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Зарегистрировать периодический свип (каждую минуту по UTC).

    Вызывается из __main__ после создания bot и session_factory.
    """
    from wrbot.scheduler.sweep import run_sweep  # локальный импорт, чтобы избежать циклов

    scheduler.add_job(
        run_sweep,
        trigger=IntervalTrigger(minutes=1, timezone=UTC),
        args=[bot, session_factory],
        id="reminder_sweep",
        name="Reminder sweep (due notifications)",
        replace_existing=True,
        misfire_grace_time=30,  # секунд, на случай задержек
    )


def register_backup_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Зарегистрировать ежечасную джобу бэкапа + heartbeat + краткой сводки (M6 TASK-0033).

    Вызывается из __main__ после создания bot и session_factory.
    """
    from wrbot.scheduler.backup import run_backup  # локальный импорт

    scheduler.add_job(
        run_backup,
        trigger=IntervalTrigger(hours=1, timezone=UTC),
        args=[bot, session_factory],
        id="backup_heartbeat",
        name="Hourly DB backup + heartbeat + summary to admin channel",
        replace_existing=True,
        misfire_grace_time=300,  # 5 мин
    )


def register_daily_dashboard_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Зарегистрировать ежедневную джобу дашборда 21:00 в ADMIN_TZ (M6 TASK-0034).

    Метрики + графики (matplotlib) + отправка в админ-канал.
    Вызывается из __main__ после создания bot и session_factory.
    """
    from apscheduler.triggers.cron import CronTrigger

    from wrbot.config import get_settings
    from wrbot.scheduler.dashboard import run_daily_dashboard  # локальный импорт

    settings = get_settings()
    tz = settings.admin_tz  # e.g. "Europe/Moscow"; CronTrigger принимает str или tzinfo

    scheduler.add_job(
        run_daily_dashboard,
        trigger=CronTrigger(hour=21, minute=0, timezone=tz),
        args=[bot, session_factory],
        id="daily_dashboard",
        name="Daily 21:00 dashboard (stats + charts) to admin channel in ADMIN_TZ",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 час
    )
