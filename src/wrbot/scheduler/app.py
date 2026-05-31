"""
APScheduler integration.

Планировщик для своевременной отправки напоминаний (NFR-1).
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Глобальный планировщик (инициализируется в __main__.py)
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    """Получить экземпляр планировщика."""
    return scheduler


def setup_scheduler() -> AsyncIOScheduler:
    """Создать и настроить планировщик."""
    global scheduler
    # TODO: M3 - настроить timezone, job stores
    scheduler = AsyncIOScheduler()
    return scheduler
