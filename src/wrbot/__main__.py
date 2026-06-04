"""
Entry point: wrbot startup.

Запускает Telegram бота с long polling (ADR-0007) и планировщиком.
"""

import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

from wrbot.bot.handlers import categories as categories_handler
from wrbot.bot.handlers import charges_create as charges_create_handler
from wrbot.bot.handlers import charges_list as charges_list_handler
from wrbot.bot.handlers import errors as errors_handler
from wrbot.bot.handlers import group as group_handler
from wrbot.bot.handlers import reminders as reminders_handler
from wrbot.bot.handlers import settings as settings_handler
from wrbot.bot.handlers import start as start_handler
from wrbot.bot.handlers import wallets as wallets_handler
from wrbot.bot.middlewares.db import DbSessionMiddleware
from wrbot.config import get_settings
from wrbot.db import get_engine, get_session_factory
from wrbot.logging import setup_logging
from wrbot.scheduler.app import (
    register_backup_job,
    register_daily_dashboard_job,
    register_sweep_job,
    setup_scheduler,
)

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
        logger.error(
            "CRITICAL: Database migrations failed. "
            "Check DATABASE_URL, DB server and alembic setup. Error: %s",
            e,
        )
        raise


async def setup_bot_commands(bot: Bot) -> None:
    """Настроить команды бота в меню Telegram.

    Приватный скоуп — как раньше.
    Group scope (TASK-0047): /getgrid для получения ID чата в группах (для notify_chat_ids).
    """

    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())

    # TASK-0047: команда для групп (любой участник может получить ID чата)
    group_commands = [
        BotCommand(command="getgrid", description="Получить ID группы для настроек напоминаний"),
    ]
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())


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
    dp.include_router(group_handler.router)
    dp.include_router(settings_handler.router)
    dp.include_router(wallets_handler.router)
    dp.include_router(categories_handler.router)
    dp.include_router(charges_create_handler.router)
    dp.include_router(charges_list_handler.router)
    dp.include_router(reminders_handler.router)

    # Глобальный обработчик ошибок (TASK-0021) — дублирование критичных в канал (TASK-0032)
    # + запись в audit для метрик дашборда (TASK-0034)
    from wrbot.bot.handlers.errors import make_global_error_handler

    # Call maker: registers error handler (bot notify 0032; session_factory for audit 0034)
    make_global_error_handler(bot, session_factory)
    dp.include_router(errors_handler.errors_router)

    # Настройка команд в меню
    await setup_bot_commands(bot)

    # Инициализация планировщика + регистрация свипа (M4 TASK-0016)
    logger.info("Initializing scheduler...")
    scheduler = setup_scheduler()
    register_sweep_job(scheduler, bot, session_factory)
    register_backup_job(scheduler, bot, session_factory)
    register_daily_dashboard_job(scheduler, bot, session_factory)
    scheduler.start()

    # Graceful shutdown по сигналам (SIGINT/SIGTERM) — критично для 24/7 в Docker / systemd (NFR-1)
    shutdown_event = asyncio.Event()

    def _request_shutdown() -> None:
        logger.info("Shutdown signal received (SIGINT/SIGTERM). Stopping gracefully...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_shutdown)

    # Запуск long polling (handle_signals=False — управляем сами)
    logger.info("Starting polling (graceful shutdown enabled)...")
    try:
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))

        # Ждём либо нормальное завершение polling, либо сигнал
        await asyncio.wait(
            [
                asyncio.create_task(shutdown_event.wait()),
                polling_task,
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not polling_task.done():
            logger.info("Stopping polling due to shutdown signal...")
            await dp.stop_polling()
            # Дождёмся завершения задачи polling
            try:
                await asyncio.wait_for(polling_task, timeout=10)
            except TimeoutError:
                logger.warning("Polling stop timed out")
    finally:
        logger.info("Shutting down resources...")
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()
        logger.info("Shutdown complete.")


def main_sync() -> None:
    """Синхронная точка входа для python -m wrbot."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
