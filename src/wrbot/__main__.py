"""
Entry point: wrbot startup.

Запускает Telegram бота с long polling (ADR-0007) и планировщиком.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from wrbot.bot.handlers import start as start_handler
from wrbot.config import settings
from wrbot.db import get_engine, get_session_factory
from wrbot.db.models import Base
from wrbot.logging import setup_logging
from wrbot.scheduler.app import setup_scheduler

logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    """Настроить команды бота в меню Telegram."""

    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())


async def main() -> None:
    """Главная функция запуска бота."""
    # Настройка логирования
    setup_logging()
    logger.info("Starting wrbot...")

    # Инициализация БД
    logger.info("Initializing database...")
    engine = get_engine(settings.database_url)
    get_session_factory(engine)

    # Создание таблиц (для dev; в prod — только через миграции)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Инициализация бота
    logger.info("Initializing bot...")
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Регистрация хэндлеров
    dp.include_router(start_handler.router)

    # Настройка команд в меню
    await setup_bot_commands(bot)

    # Инициализация планировщика
    logger.info("Initializing scheduler...")
    scheduler = setup_scheduler()
    scheduler.start()

    # Запуск long polling
    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await bot.session.close()
        await engine.dispose()


def main_sync() -> None:
    """Синхронная точка входа для python -m wrbot."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
