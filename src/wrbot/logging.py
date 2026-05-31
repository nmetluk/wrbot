"""
Logging configuration.

Настройка структурированного логирования в файл и консоль.
"""

import logging
import logging.config
from pathlib import Path
from typing import Literal

from wrbot.config import settings


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = None,
    log_file: str | None = None,
) -> None:
    """
    Настроить логирование.

    Args:
        level: Уровень логирования (по умолчанию из настроек)
        log_file: Путь к файлу логов (по умолчанию из настроек)
    """
    if level is None:
        level = settings.log_level
    if log_file is None:
        log_file = settings.log_file

    # Создаём директорию для логов
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_level = logging.getLevelName(level)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "formatter": "detailed",
                    "filename": log_file,
                    "maxBytes": 10 * 1024 * 1024,  # 10 MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": log_level,
                "handlers": ["console", "file"],
            },
            "loggers": {
                "aiogram": {
                    "level": "WARNING",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "apscheduler": {
                    "level": "WARNING",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "handlers": ["file"],  # SQL логи только в файл
                    "propagate": False,
                },
            },
        }
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging configured: level=%s, file=%s", level, log_file)
