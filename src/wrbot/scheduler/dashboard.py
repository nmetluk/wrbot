"""
Daily dashboard job (M6, TASK-0034).

В 21:00 по ADMIN_TZ: собирает метрики (stats), рендерит графики (charts),
отправляет текстовый саммари + альбом/фото в админ-канал через AdminNotifier.
Ошибки изолированы (джоба не падает, бот жив). No-op если нет ADMIN_CHANNEL_ID.
"""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wrbot.config import get_settings
from wrbot.services.admin_notify import AdminNotifier
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
from wrbot.services.stats import (
    get_charges_created_daily,
    get_daily_new_and_active_users,
    get_errors_daily,
    get_payments_daily,
    get_period_distribution,
    get_reminders_sent_daily,
    get_top_categories,
    get_user_growth_30d,
)

logger = logging.getLogger(__name__)


async def run_daily_dashboard(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Ежедневная джоба 21:00 (в ADMIN_TZ): дашборд со статистикой и графиками.
    """
    settings = get_settings()
    notifier = AdminNotifier(bot)

    if settings.admin_channel_id is None:
        logger.debug("ADMIN_CHANNEL_ID not set — daily dashboard job is no-op")
        return

    start = datetime.utcnow()
    ts = start.strftime("%Y-%m-%d")

    try:
        # 1. Собрать метрики (нужна сессия)
        async with session_factory() as session:
            user_growth = await get_user_growth_30d(session, start)
            daily_activity = await get_daily_new_and_active_users(session, days=7, now=start)
            charges_created = await get_charges_created_daily(session, days=14, now=start)
            payments = await get_payments_daily(session, days=7, now=start)
            period_dist = await get_period_distribution(session)
            top_cats = await get_top_categories(session, limit=5, by="count")
            reminders = await get_reminders_sent_daily(session, days=7, now=start)
            errors = await get_errors_daily(session, days=7, now=start)

        # 2. Рендер графиков в thread (matplotlib sync, не блокируем loop)
        def _render_charts() -> list[tuple[bytes, str]]:
            charts: list[tuple[bytes, str]] = []
            try:
                charts.append((render_user_growth_chart(user_growth), "Рост пользователей (30д)"))
            except Exception:
                logger.exception("Failed to render user growth chart")
            try:
                charts.append(
                    (render_daily_activity_chart(daily_activity), "Новые/активные пользователи")
                )
            except Exception:
                logger.exception("Failed to render activity chart")
            try:
                charts.append(
                    (render_charges_created_chart(charges_created), "Создано списаний (14д)")
                )
            except Exception:
                logger.exception("Failed to render created chart")
            try:
                charts.append((render_payments_chart(payments), "Оплачено за день"))
            except Exception:
                logger.exception("Failed to render payments chart")
            try:
                charts.append((render_period_pie(period_dist), "Распределение по периодам"))
            except Exception:
                logger.exception("Failed to render period pie")
            try:
                charts.append((render_top_categories_chart(top_cats), "Топ категорий"))
            except Exception:
                logger.exception("Failed to render top cats chart")
            try:
                charts.append((render_reminders_chart(reminders), "Напоминания за день"))
            except Exception:
                logger.exception("Failed to render reminders chart")
            try:
                charts.append((render_errors_chart(errors), "Ошибки за день"))
            except Exception:
                logger.exception("Failed to render errors chart")
            return charts

        chart_images = await asyncio.to_thread(_render_charts)

        # 3. Краткий текстовый саммари (ключевые числа)
        total_users = user_growth[-1]["cumulative"] if user_growth else 0
        today_activity = daily_activity[-1] if daily_activity else {"new": 0, "active": 0}
        created_today = charges_created[-1]["count"] if charges_created else 0
        paid_today = payments[-1]["count"] if payments else 0
        paid_sum = payments[-1]["sum"] if payments else 0.0
        reminders_today = reminders[-1]["count"] if reminders else 0
        errors_today = errors[-1]["count"] if errors else 0

        summary = (
            f"📊 <b>Дашборд {ts}</b> (21:00 {settings.admin_tz})\n\n"
            f"👥 Пользователей всего: <b>{total_users}</b>\n"
            f"🆕 Новых сегодня: <b>{today_activity['new']}</b> | "
            f"Активных: <b>{today_activity['active']}</b>\n"
            f"📝 Создано списаний: <b>{created_today}</b>\n"
            f"✅ Оплачено: <b>{paid_today}</b> (сумма ~{paid_sum:.0f})\n"
            f"🔔 Напоминаний отправлено: <b>{reminders_today}</b>\n"
            f"🚨 Ошибок: <b>{errors_today}</b>\n\n"
            "Подробности — на графиках ниже."
        )

        # 4. Отправка (изолировано внутри notifier)
        await notifier.send_text(summary)

        if chart_images:
            media: list[InputMediaPhoto] = []
            for img_bytes, caption in chart_images:
                media.append(
                    InputMediaPhoto(
                        media=BufferedInputFile(img_bytes, filename="chart.png"),
                        caption=caption,
                    )
                )
            # Отправляем группой (альбом); если очень много — notifier/Telegram ограничат, но 8 ок
            await notifier.send_media_group(media)

        logger.info("Daily dashboard completed for %s", ts)

    except Exception:
        logger.exception("Daily dashboard job failed (errors isolated, bot continues)")
        # Не падаем — не роняем scheduler
