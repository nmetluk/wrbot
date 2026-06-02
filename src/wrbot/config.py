"""
Configuration management.

Загрузка настроек из переменных окружения и .env файла.
Все секреты хранятся в окружении, не хардкодятся (NFR-6).

Импорт пакета НЕ требует секретов — настройки загружаются лениво
при первом вызове get_settings().
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Загружаем .env из корня проекта (или директории запуска)
load_dotenv()


def _expand_db_url(url: str) -> str:
    """Раскрыть тильду в database_url."""
    if url.startswith("sqlite") and "~" in url:
        # sqlite+aiosqlite:///~/path -> sqlite+aiosqlite:////full/path
        parts = url.split("///", 1)
        if len(parts) == 2:
            scheme, path = parts
            expanded = Path(path).expanduser().absolute()
            return f"{scheme}////{expanded}"
    return url


class Settings(BaseSettings):
    """
    Настройки приложения.

    Загружаются из переменных окружения.
    """

    # Telegram Bot - обязателен, без дефолта
    bot_token: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/wrbot.db"

    # Timezone (ADR-0004)
    default_timezone: str = "Europe/Moscow"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str = "logs/wrbot.log"

    # Лимиты справочников (M2)
    max_wallets: int = 20
    max_categories: int = 20

    # Лимиты списаний (M3)
    max_charges: int = 50

    # Admin channel for M6 observability (ADR-0008, TASK-0031)
    # If None — all admin notifies are no-op (safe for tests/CI/local without channel)
    admin_channel_id: int | None = None
    admin_tz: str = "Europe/Moscow"

    # Project paths
    base_dir: Path = Path(__file__).parent.parent.parent
    src_dir: Path = Path(__file__).parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @model_validator(mode="after")
    def expand_database_url(self) -> "Settings":
        """Раскрыть тильду в database_url после загрузки настроек."""
        self.database_url = _expand_db_url(self.database_url)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Получить экземпляр настроек (singleton с ленивой загрузкой).

    Настройки загружаются при первом вызове, subsequent calls return cached instance.
    Если BOT_TOKEN не задан, Pydantic выбросит ValidationError при первом вызове.

    Returns:
        Settings с загруженными значениями из окружения
    """
    return Settings()
