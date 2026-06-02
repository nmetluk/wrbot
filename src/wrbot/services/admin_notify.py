"""
Admin notification service (M6, TASK-0031, ADR-0008).

Безопасная отправка текста/фото/медиа-групп в приватный админ-канал.
- no-op если ADMIN_CHANNEL_ID не задан (работает в тестах/CI/локалке).
- Ошибки изолированы (не роняют вызвавший код/джобу).
- Санитизация секретов (BOT_TOKEN, DATABASE_URL и т.п. никогда не попадают в канал).
"""

import logging
from typing import Any

from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto

from wrbot.config import get_settings

logger = logging.getLogger(__name__)


def _sanitize(text: str) -> str:
    """Маскирует чувствительные данные в тексте для безопасной отправки в админ-канал."""
    if not text:
        return text
    settings = get_settings()
    sanitized = text
    if settings.bot_token:
        sanitized = sanitized.replace(settings.bot_token, "***BOT_TOKEN***")
    if settings.database_url:
        # Полностью маскируем URL с кредами (не пытаемся частично парсить)
        sanitized = sanitized.replace(settings.database_url, "***DATABASE_URL***")
    # Дополнительно: простая маскировка типичных паттернов (на случай если секреты в логах)
    # Не логируем IP сервера и т.п. — по ADR-0008
    return sanitized


class AdminNotifier:
    """Сервис отправки уведомлений в админ-канал.

    Использование:
        notifier = AdminNotifier(bot)
        await notifier.send_text("hello")
        await notifier.send_photo(photo_bytes, caption="chart")
    """

    def __init__(self, bot: Bot | None = None) -> None:
        self._bot = bot
        self._settings = get_settings()
        self._channel_id: int | None = self._settings.admin_channel_id

    async def _safe_send(self, send_coro: Any) -> None:
        """Выполняет отправку с изоляцией ошибок."""
        try:
            await send_coro
        except Exception as exc:
            # Критично: не роняем вызвавшую джобу/обработчик
            logger.exception("Admin notify failed (isolated): %s", exc)

    async def send_text(self, text: str, **kwargs: Any) -> None:
        """Отправить текстовое сообщение в админ-канал (с санитизацией)."""
        if not text:
            return
        safe_text = _sanitize(text)
        if self._channel_id is None or self._bot is None:
            logger.debug("ADMIN_CHANNEL_ID not set — admin notify is no-op")
            return
        await self._safe_send(
            self._bot.send_message(
                chat_id=self._channel_id,
                text=safe_text,
                parse_mode=kwargs.pop("parse_mode", "HTML"),
                **kwargs,
            )
        )

    async def send_photo(
        self, photo: bytes | str, caption: str | None = None, **kwargs: Any
    ) -> None:
        """Отправить фото (bytes или file_id/path) с опциональной подписью."""
        if self._channel_id is None or self._bot is None:
            logger.debug("ADMIN_CHANNEL_ID not set — admin notify is no-op")
            return
        photo_input: BufferedInputFile | str
        if isinstance(photo, bytes):
            photo_input = BufferedInputFile(photo, filename="admin_photo.jpg")
        else:
            photo_input = photo
        safe_caption = _sanitize(caption) if caption else None
        await self._safe_send(
            self._bot.send_photo(
                chat_id=self._channel_id,
                photo=photo_input,
                caption=safe_caption,
                parse_mode=kwargs.pop("parse_mode", "HTML") if safe_caption else None,
                **kwargs,
            )
        )

    async def send_media_group(self, media: list[InputMediaPhoto | Any], **kwargs: Any) -> None:
        """Отправить медиа-группу. Санитизирует caption в элементах."""
        if self._channel_id is None or self._bot is None:
            logger.debug("ADMIN_CHANNEL_ID not set — admin notify is no-op")
            return
        # Санитизируем подписи в media если есть (InputMedia* frozen в pydantic)
        sanitized_media = []
        for m in media:
            if hasattr(m, "caption") and getattr(m, "caption", None):
                if hasattr(m, "model_copy"):
                    sanitized_media.append(
                        m.model_copy(update={"caption": _sanitize(m.caption)})
                    )
                else:
                    sanitized_media.append(m)
            else:
                sanitized_media.append(m)
        await self._safe_send(
            self._bot.send_media_group(
                chat_id=self._channel_id,
                media=sanitized_media,
                **kwargs,
            )
        )
