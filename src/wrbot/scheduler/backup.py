"""
Hourly backup job (M6, TASK-0033).

Выполняет бэкап, ротацию, отправляет статус + heartbeat + краткую сводку в админ-канал.
Ошибки изолированы (джоба не падает).
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wrbot.services.admin_notify import AdminNotifier
from wrbot.services.backup import create_backup, rotate_backups
from wrbot.services.stats import get_hourly_summary

logger = logging.getLogger(__name__)


async def run_backup(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Ежечасная джоба: бэкап + статус в канал + heartbeat + сводка.
    """
    notifier = AdminNotifier(bot)
    start = datetime.utcnow()
    ts = start.strftime("%Y%m%d-%H%M")

    # 1. Создать бэкап (sync op в thread, чтобы не блокировать event loop)
    backup_info = await asyncio.to_thread(create_backup)

    # 2. Ротация (sync)
    await asyncio.to_thread(rotate_backups)

    # 3. Краткая сводка (нужна сессия)
    summary = {
        "total_users": 0,
        "active_charges": 0,
        "charges_created_last_hour": 0,
        "charges_paid_last_hour": 0,
    }
    try:
        async with session_factory() as session:
            summary = await get_hourly_summary(session, start)
    except Exception:
        logger.exception("Failed to compute hourly summary")

    # 4. Сформировать сообщение
    if backup_info.get("success"):
        size_kb = backup_info.get("size", 0) / 1024
        file_name = Path(backup_info.get("file", "")).name if backup_info.get("file") else "unknown"
        status = f"✅ Бэкап ОК: {file_name}, {size_kb:.1f} KB"
    else:
        status = f"❌ Ошибка бэкапа: {backup_info.get('error', 'unknown')}"

    msg = (
        f"🗄️ {status}\n"
        f"🟢 Бот работает (heartbeat {ts} UTC)\n\n"
        f"📊 Сводка за час:\n"
        f"• Пользователей всего: {summary['total_users']}\n"
        f"• Активных списаний: {summary['active_charges']}\n"
        f"• Создано списаний: {summary['charges_created_last_hour']}\n"
        f"• Отмечено оплат: {summary['charges_paid_last_hour']}"
    )

    # 5. Отправить (ошибки в notifier изолированы)
    try:
        await notifier.send_text(msg)
    except Exception:
        logger.exception("Failed to send backup/heartbeat to admin channel (isolated)")

    logger.info("Backup job completed: success=%s", backup_info.get("success"))
