"""Database session middleware for dependency injection in aiogram handlers."""

import logging
from collections.abc import Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для внедрения AsyncSession в контекст хэндлера.

    На каждый update открывает новую сессию, кладёт её в data["session"].
    При успехе коммитит, при исключении — откатывает. Всегда закрывает сессию.
    """

    __slots__ = ("session_factory",)

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """
        Инициализация middleware.

        Args:
            session_factory: Фабрика сессий SQLAlchemy (из get_session_factory)
        """
        super().__init__()
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Выполнить хэндлер с открытой сессией БД.

        Сессия создаётся перед хэндлером и закрывается после.
        При исключении откатывает транзакцию.
        """
        async with self.session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
