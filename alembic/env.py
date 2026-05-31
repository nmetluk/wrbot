"""
Alembic environment configuration.

Настройка контекста миграций для SQLAlchemy 2.0 async.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from wrbot.config import settings
from wrbot.db.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем метаданные моделей для autogenerate
target_metadata = Base.metadata

# Беру database_url из настроек, а не из alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)


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


def do_run_migrations(connection) -> None:
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

    В этом режиме создаётся объект Engine и вызываются миграции.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
