"""
Тесты конфигурации.
"""

from wrbot.config import settings


def test_settings_has_bot_token(monkeypatch) -> None:
    """Проверка что BOT_TOKEN загружается из окружения."""
    # Устанавливаем тестовый токен
    monkeypatch.setenv("BOT_TOKEN", "test_token_123")

    # Пересоздаём settings для чтения нового значения
    from wrbot.config import Settings

    new_settings = Settings()

    assert new_settings.bot_token == "test_token_123"


def test_settings_defaults() -> None:
    """Проверка дефолтных значений настроек."""
    assert settings.default_timezone == "Europe/Moscow"
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert "wrbot.log" in settings.log_file
