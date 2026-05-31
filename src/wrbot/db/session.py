"""
Database session management.

Создание движка и фабрики сессий для SQLAlchemy 2.0 async.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_engine(database_url: str) -> AsyncEngine:
    """
    Создать async двигатель SQLAlchemy.

    Args:
        database_url: URL БД (sqlite+aiosqlite:///... или postgresql+asyncpg://...)

    Returns:
        AsyncEngine для SQLAlchemy
    """
    return create_async_engine(
        database_url,
        echo=False,  # True для SQL-лога в dev
        # Для SQLite нужно включать某些 опции
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Создать фабрику сессий.

    Args:
        engine: AsyncEngine из get_engine()

    Returns:
        Фабрика AsyncSession
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
