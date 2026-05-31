"""
Configuration management.

Загрузка настроек из переменных окружения и .env файла.
Все секреты хранятся в окружении, не хардкодятся (NFR-6).
"""

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Загружаем .env из корня проекта (или директории запуска)
load_dotenv()


class Settings(BaseSettings):
    """
    Настройки приложения.

    Загружаются из переменных окружения с дефолтными значениями.
    """

    # Telegram Bot
    bot_token: str = "test_token"  # Required for bot, default for tests

    # Database
    database_url: str = "sqlite+aiosqlite:///~/.local/share/wrbot/wrbot.db"

    # Timezone (ADR-0004)
    default_timezone: str = "Europe/Moscow"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str = "logs/wrbot.log"

    # Project paths
    base_dir: Path = Path(__file__).parent.parent.parent
    src_dir: Path = Path(__file__).parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


def get_settings() -> Settings:
    """
    Получить экземпляр настроек (singleton).

    Returns:
        Settings с загруженными значениями из окружения
    """
    return Settings()


# Глобальный экземпляр настроек
settings = get_settings()
