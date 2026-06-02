"""
Тесты для AdminNotifier (TASK-0031, ADR-0008).

- no-op без ADMIN_CHANNEL_ID
- вызовы bot.send_* с правильным chat_id
- изоляция ошибок (не падают)
- санитизация секретов
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.types import BufferedInputFile

from wrbot.config import Settings, get_settings
from wrbot.services.admin_notify import AdminNotifier, _sanitize


def _make_mock_bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_media_group = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_noop_when_no_channel_id(monkeypatch):
    """Если ADMIN_CHANNEL_ID не задан — no-op, без вызовов бота."""
    monkeypatch.setenv("BOT_TOKEN", "test123")
    monkeypatch.delenv("ADMIN_CHANNEL_ID", raising=False)
    # Пересоздать settings
    get_settings.cache_clear()
    settings = Settings()
    assert settings.admin_channel_id is None

    bot = _make_mock_bot()
    notifier = AdminNotifier(bot)
    await notifier.send_text("hello admin")
    await notifier.send_photo(b"fake", "chart")
    bot.send_message.assert_not_called()
    bot.send_photo.assert_not_called()


@pytest.mark.asyncio
async def test_sends_with_correct_chat_id(monkeypatch):
    """Когда ID задан — вызывает send с chat_id = ADMIN_CHANNEL_ID."""
    monkeypatch.setenv("BOT_TOKEN", "test123")
    monkeypatch.setenv("ADMIN_CHANNEL_ID", "123456789")
    get_settings.cache_clear()

    bot = _make_mock_bot()
    notifier = AdminNotifier(bot)

    await notifier.send_text("test message", parse_mode="HTML")
    bot.send_message.assert_awaited_once()
    call = bot.send_message.call_args
    assert call.kwargs["chat_id"] == 123456789
    assert "test message" in call.kwargs["text"]

    # photo
    await notifier.send_photo(b"\x89PNG...", caption="image")
    bot.send_photo.assert_awaited_once()
    pcall = bot.send_photo.call_args
    assert pcall.kwargs["chat_id"] == 123456789
    assert isinstance(pcall.kwargs["photo"], BufferedInputFile)


@pytest.mark.asyncio
async def test_error_is_isolated(monkeypatch):
    """Ошибка отправки логируется, но не падает вызывающий код."""
    monkeypatch.setenv("BOT_TOKEN", "test123")
    monkeypatch.setenv("ADMIN_CHANNEL_ID", "999")
    get_settings.cache_clear()

    bot = _make_mock_bot()
    bot.send_message.side_effect = RuntimeError("channel down")
    notifier = AdminNotifier(bot)

    # Не должно кидать
    await notifier.send_text("will fail but isolated")
    # Вызов был
    bot.send_message.assert_awaited_once()


def test_sanitize_masks_secrets(monkeypatch):
    """_sanitize маскирует BOT_TOKEN и DATABASE_URL."""
    monkeypatch.setenv("BOT_TOKEN", "secret_bot_token_123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/wrbot")
    get_settings.cache_clear()

    text = (
        "Error with token secret_bot_token_123 and db postgresql+asyncpg://user:pass@db:5432/wrbot"
    )
    sanitized = _sanitize(text)
    assert "secret_bot_token_123" not in sanitized
    assert "postgresql+asyncpg://user:pass@db:5432/wrbot" not in sanitized
    assert "***BOT_TOKEN***" in sanitized
    assert "***DATABASE_URL***" in sanitized


@pytest.mark.asyncio
async def test_media_group_sanitizes_captions(monkeypatch):
    """send_media_group санитизирует caption в медиа."""
    monkeypatch.setenv("BOT_TOKEN", "tok")
    monkeypatch.setenv("ADMIN_CHANNEL_ID", "42")
    get_settings.cache_clear()

    bot = _make_mock_bot()
    notifier = AdminNotifier(bot)

    from aiogram.types import InputMediaPhoto

    media = [
        InputMediaPhoto(media=b"1", caption="with tok secret"),
        InputMediaPhoto(media=b"2", caption="clean"),
    ]
    await notifier.send_media_group(media)
    bot.send_media_group.assert_awaited_once()
    mcall = bot.send_media_group.call_args
    sent_media = mcall.kwargs["media"]
    assert sent_media[0].caption is not None
    assert "tok" not in sent_media[0].caption
    assert "***BOT_TOKEN***" in sent_media[0].caption or "secret" not in sent_media[0].caption
