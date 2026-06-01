"""
Entry point: wrbot startup.

Запускает Telegram бота с long polling (ADR-0007) и планировщиком.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from wrbot.bot.handlers import categories as categories_handler
from wrbot.bot.handlers import charges_create as charges_create_handler
from wrbot.bot.handlers import charges_list as charges_list_handler
from wrbot.bot.handlers import settings as settings_handler
from wrbot.bot.handlers import start as start_handler
from wrbot.bot.handlers import wallets as wallets_handler
from wrbot.bot.middlewares.db import DbSessionMiddleware
from wrbot.config import get_settings
from wrbot.db import get_engine, get_session_factory
from wrbot.logging import setup_logging
from wrbot.scheduler.app import setup_scheduler

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Выполнить миграции Alembic при старте."""
    from alembic import command
    from alembic.config import Config

    settings = get_settings()
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations upgraded to head")
    except Exception as e:
        logger.error("Migration failed: %s", e)
        raise


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
    # Получаем настройки (теперь лениво)
    settings = get_settings()

    # Настройка логирования
    setup_logging()
    logger.info("Starting wrbot...")

    # Выполняем миграции при старте
    logger.info("Running database migrations...")
    await run_migrations()

    # Инициализация БД
    logger.info("Initializing database...")
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    # Инициализация бота
    logger.info("Initializing bot...")
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Регистрация middleware (до хэндлеров!)
    dp.update.middleware(DbSessionMiddleware(session_factory))

    # Регистрация хэндлеров
    dp.include_router(start_handler.router)
    dp.include_router(settings_handler.router)
    dp.include_router(wallets_handler.router)
    dp.include_router(categories_handler.router)
    dp.include_router(charges_create_handler.router)
    dp.include_router(charges_list_handler.router)

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
