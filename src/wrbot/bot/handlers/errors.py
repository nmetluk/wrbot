"""
Global error handler for the bot (TASK-0021, NFR-1).

Ловит необработанные исключения из хэндлеров и middleware,
логирует с контекстом (через structlog/logging), отвечает пользователю
понятным сообщением. Не даёт боту упасть.
Критичные ошибки дублируются в админ-канал (TASK-0032).
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Bot, Router
from aiogram.types import CallbackQuery, ErrorEvent

from wrbot.bot.texts import Texts
from wrbot.services.admin_notify import AdminNotifier

logger = logging.getLogger(__name__)

errors_router = Router(name="errors")


def make_global_error_handler(bot: Bot | None = None) -> Callable[[ErrorEvent], Awaitable[None]]:
    """Factory: registers error handler (with bot for admin notify duplicate)."""

    @errors_router.error()
    async def global_error_handler(event: ErrorEvent) -> None:
        """
        Глобальный обработчик ошибок aiogram.

        Логирует исключение с максимально возможным контекстом (update, user, chat).
        Пытается отправить пользователю дружелюбное сообщение.
        Не перевыбрасывает исключение — бот продолжает работу.
        """
        exception = event.exception
        # event.update может быть aiogram.types.Update или None
        update = getattr(event, "update", None)

        # Логируем с контекстом (для расследования в 24/7)
        log_context: dict[str, Any] = {"exception_type": type(exception).__name__}
        if update:
            if hasattr(update, "message") and update.message:
                log_context["chat_id"] = update.message.chat.id
                log_context["user_id"] = (
                    update.message.from_user.id if update.message.from_user else None
                )
                log_context["text"] = update.message.text[:100] if update.message.text else None
            elif hasattr(update, "callback_query") and update.callback_query:
                cq: CallbackQuery = update.callback_query
                log_context["chat_id"] = cq.message.chat.id if cq.message else None
                log_context["user_id"] = cq.from_user.id if cq.from_user else None
                log_context["data"] = cq.data[:50] if cq.data else None

        logger.error(
            "Unhandled error in bot update: %s",
            exception,
            extra=log_context,
            exc_info=True,
        )

        # Пытаемся ответить пользователю (не падаем, если не получилось)
        try:
            if update and update.message:
                await update.message.answer(Texts.error_generic)
            elif update and update.callback_query:
                cq = update.callback_query
                await cq.answer(Texts.error_generic, show_alert=True)
                # Также можно отредактировать сообщение, но answer достаточно
        except Exception as reply_exc:
            logger.warning("Failed to send error message to user: %s", reply_exc)

        # Duplicate critical error to admin channel (TASK-0032, via AdminNotifier)
        if bot:
            try:
                notifier = AdminNotifier(bot)
                await notifier.send_text(
                    f"🚨 <b>Critical bot error</b>\n"
                    f"Type: {type(exception).__name__}\n"
                    f"User: {log_context.get('user_id')}, Chat: {log_context.get('chat_id')}\n"
                    f"Details: {str(exception)[:300]}"
                )
            except Exception as notify_exc:
                logger.warning("Failed to duplicate error to admin channel: %s", notify_exc)

        # Важно: НЕ re-raise, иначе update упадёт и polling может пострадать

    return global_error_handler
