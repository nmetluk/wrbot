"""
Global error handler for the bot (TASK-0021, NFR-1).

Ловит необработанные исключения из хэндлеров и middleware,
логирует с контекстом (через structlog/logging), отвечает пользователю
понятным сообщением. Не даёт боту упасть.
"""

import logging
from typing import Any

from aiogram import Router
from aiogram.types import CallbackQuery, ErrorEvent

from wrbot.bot.texts import Texts

logger = logging.getLogger(__name__)

errors_router = Router(name="errors")


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

    # Важно: НЕ re-raise, иначе update упадёт и polling может пострадать
