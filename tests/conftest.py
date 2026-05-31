"""
Shared pytest fixtures and configuration.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from wrbot.db import get_engine
from wrbot.db.models import Base


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Создать тестовый двигатель SQLite в памяти.

    Все таблицы создаются заново для каждого теста.
    """
    engine = get_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


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
