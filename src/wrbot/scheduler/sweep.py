"""
Sweep job for sending due reminders (TASK-0016).

Вызывается планировщиком каждую минуту (UTC).
- Использует готовую due-логику из services.reminders (TASK-0014).
- Отправляет через aiogram Bot + клавиатуру из TASK-0015.
- Идемпотентность через SentReminderRepository (защита от рестартов и повторных тиков).
- Изоляция ошибок: сбой по одному пользователю не роняет весь свип.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, cast

from wrbot.bot.keyboards import get_reminder_actions_keyboard
from wrbot.bot.texts import Texts
from wrbot.repositories.sent_reminders import SentReminderRepository
from wrbot.services.reminders import get_due_reminders_today

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from wrbot.models import Charge, User  # only for cast() in sweep

logger = logging.getLogger(__name__)


async def run_sweep(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Основной свип: выбрать due напоминания и отправить их.

    Должен быть неблокирующим. Ошибки на одного пользователя логируются и пропускаются.
    """
    now_utc: datetime = datetime.now(UTC)
    today: date = now_utc.date()

    async with session_factory() as session:
        sent_repo = SentReminderRepository(session)

        try:
            due_items = await get_due_reminders_today(session, today, sent_repo)
        except Exception:
            logger.exception("Failed to compute due reminders in sweep")
            return

        if not due_items:
            logger.debug("Sweep at %s: no due reminders", now_utc)
            return

        sent_count = 0
        for raw_item in due_items:
            item: dict[str, Any] = cast("dict[str, Any]", raw_item)
            charge = cast("Charge", item["charge"])
            user = cast("User", item["user"])
            target_date = cast("date", item["target_date"])
            days_before = cast("int", item["days_before"])

            # Подготовка текста (wallet name упрощённо; в будущем можно дообогатить join'ом)
            wallet_label = f"#{charge.wallet_id}"
            text = Texts.reminder_notification.format(
                name=charge.name,
                amount=str(charge.amount),
                wallet=wallet_label,
                next_date=charge.next_date,
            )
            keyboard = get_reminder_actions_keyboard(charge.id)

            try:
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=text,
                    reply_markup=keyboard,
                )
                # Фиксируем отправку только после успешной доставки
                await sent_repo.record(charge.id, target_date, days_before)
                sent_count += 1
                logger.info(
                    "Sent reminder: user=%s, charge=%s (%s), days_before=%s",
                    user.tg_id,
                    charge.id,
                    charge.name,
                    days_before,
                )
            except Exception as exc:
                # Изоляция: не роняем весь свип
                logger.warning(
                    "Failed to send reminder user=%s charge=%s: %s",
                    user.tg_id,
                    charge.id,
                    exc,
                )
                # Не записываем в sent_reminders — повторим в следующем тике

        if sent_count:
            logger.info("Sweep completed: sent %d reminders at %s", sent_count, now_utc)
