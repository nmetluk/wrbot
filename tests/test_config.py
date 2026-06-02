"""
Тесты конфигурации.
"""

import os

from wrbot.config import Settings, get_settings

os.environ.setdefault("BOT_TOKEN", "test_token_for_config_tests")


def test_settings_has_bot_token(monkeypatch) -> None:
    """Проверка что BOT_TOKEN загружается из окружения."""
    # Устанавливаем тестовый токен
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")

    # Пересоздаём settings для чтения нового значения
    new_settings = Settings()

    assert new_settings.bot_token == "test_token_123"


def test_settings_defaults(monkeypatch) -> None:
    """Проверка дефолтных значений настроек."""
    monkeypatch.delenv("ADMIN_CHANNEL_ID", raising=False)
    monkeypatch.delenv("ADMIN_TZ", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.default_timezone == "Europe/Moscow"
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert "wrbot.log" in settings.log_file
    # M6 admin (TASK-0031)
    assert settings.admin_channel_id is None
    assert settings.admin_tz == "Europe/Moscow"
