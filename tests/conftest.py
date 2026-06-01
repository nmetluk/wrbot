"""
Shared pytest fixtures and configuration.

Тесты используют Alembic миграции для создания схемы БД.
"""

# Устанавливаем переменные окружения ДО импорта wrbot
import os
import tempfile
from collections.abc import AsyncGenerator
from contextlib import suppress
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from wrbot.db import get_engine

os.environ.setdefault("BOT_TOKEN", "test_token_for_tests")


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Создать тестовый двигатель SQLite в файле и выполнить миграции.

    Все таблицы создаются через Alembic миграции.
    """
    import asyncio
    import sys

    from alembic import command
    from alembic.config import Config

    # Создаём временный файл для БД для этого теста
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        temp_db_path = temp_db.name

    # Выполняем миграции на БД в отдельном потоке
    # чтобы избежать конфликта event loops
    def run_migrations():
        project_root = Path(__file__).parent.parent
        alembic_dir = project_root / "alembic"
        alembic_ini = project_root / "alembic.ini"

        alembic_cfg = Config(str(alembic_ini))
        # Используем синхронный URL для alembic (sqlite:// вместо sqlite+aiosqlite://)
        sync_db_url = f"sqlite:///{temp_db_path}"
        alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)
        alembic_cfg.set_main_option("script_location", str(alembic_dir))

        # Добавляем src в PYTHONPATH для импорта моделей
        sys.path.insert(0, str(project_root / "src"))

        command.upgrade(alembic_cfg, "head")

    # Запускаем миграции в отдельном потоке
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_migrations)

    # Создаём engine ПОСЛЕ миграций
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    os.environ["DATABASE_URL"] = db_url
    engine = get_engine(db_url)

    yield engine

    await engine.dispose()

    # Удаляем временный файл
    with suppress(OSError, FileNotFoundError):
        Path(temp_db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def db_session(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Создать новую сессию для каждого теста.

    Транзакция откатывается после каждого теста.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        # Rollback после теста
        await session.rollback()


# Алиас для совместимости с именем в тестах репозиториев
async_session = db_session
