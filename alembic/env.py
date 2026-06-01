"""
Alembic environment configuration.

Настройка контекста миграций для SQLAlchemy 2.0 async.
Поддерживает как async (sqlite+aiosqlite), так и sync (sqlite) URL.
"""

# Добавляем src в PYTHONPATH для импорта wrbot при запуске миграций
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, str(Path(__file__).parent.parent))

from wrbot.db.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем метаданные моделей для autogenerate
target_metadata = Base.metadata

# Берём database_url из alembic config (устанавливается в conftest.py или __main__.py)
# Если не установлен, пробуем получить из settings (для продакшена)
db_url = config.get_main_option("sqlalchemy.url")
if not db_url:
    from wrbot.config import settings

    db_url = settings.database_url
    config.set_main_option("sqlalchemy.url", db_url)

# Определяем, async это URL или нет
is_async = db_url.startswith("sqlite+aiosqlite") or db_url.startswith("postgresql+asyncpg")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    В этом режиме не создаётся соединение с БД.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнить миграции с установленным соединением."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    В этом режиме создаётся Engine (async или sync) и вызываются миграции.
    """
    import asyncio

    if is_async:
        # Async режим (sqlite+aiosqlite, postgresql+asyncpg)
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async def run_async_migration() -> None:
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

        # Проверяем, запущен ли уже event loop (например, в pytest)
        try:
            loop = asyncio.get_running_loop()
            # Если loop уже есть, создаём задачу и ждём завершения через future
            result = loop.create_task(run_async_migration())
            # Используем синхронное ожидание через concurrent.futures
            while not result.done():
                import time

                time.sleep(0.01)
            # Проверяем на исключения
            if result.exception():
                raise result.exception()
        except RuntimeError:
            # Если нет loop, запускаем новый
            asyncio.run(run_async_migration())
    else:
        # Sync режим (sqlite, postgresql)
        connectable = create_engine(
            db_url,
            poolclass=pool.NullPool,
        )

        with connectable.begin() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
