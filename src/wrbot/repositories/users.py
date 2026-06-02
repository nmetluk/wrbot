"""
User repository.

Доступ к данным пользователей с изоляцией по tg_id (FR-13).
"""

import logging
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import User
from wrbot.repositories.audit_log import (
    ACTION_SETTINGS_DAYS,
    ACTION_SETTINGS_NOTIFY_TIME,
    ACTION_SETTINGS_TZ,
    AuditLogRepository,
)

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.

        Args:
            session: Сессия БД SQLAlchemy
        """
        self._session = session

    async def get_or_create(
        self,
        tg_id: int,
        *,
        notify_time: time = time(10, 0),
        tz: str = "Europe/Moscow",
        global_days: str = "[5,3,1]",
        create_default_wallet: bool = True,
    ) -> User:
        """
        Получить существующего пользователя или создать нового.

        Идемпотентен: при повторном вызове с тем же tg_id возвращает существующего.
        При создании нового пользователя (и только тогда) создаёт дефолтный кошелёк
        «Основная карта» (TASK-0035 hotfix). Не пересоздаёт, если пользователь уже
        существовал (даже если потом удалил все кошельки).

        Args:
            tg_id: Telegram ID пользователя
            notify_time: Время уведомлений (дефолт 10:00)
            tz: Часовой пояс (дефолт Europe/Moscow)
            global_days: Дни напоминаний как JSON (дефолт [5,3,1])
            create_default_wallet: Создавать ли «Основная карта» при создании пользователя
                (по умолчанию True для онбординга; в тестах можно False).

        Returns:
            User: существующий или вновь созданный пользователь
        """
        # Сначала пробуем получить существующего
        result = await self._session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user is not None:
            logger.debug("User found: tg_id=%s", tg_id)
            return user

        # Создаём нового
        user = User(
            tg_id=tg_id,
            notify_time=notify_time,
            tz=tz,
            global_days=global_days,
        )
        self._session.add(user)
        await self._session.flush()
        logger.info("Created user: tg_id=%s", tg_id)

        if create_default_wallet:
            # Создаём дефолтный кошелёк только для brand-new пользователя (в той же сессии)
            from .wallets import WalletRepository

            wrepo = WalletRepository(self._session)
            try:
                await wrepo.create(tg_id, "Основная карта")
                logger.info("Created default wallet for new user: tg_id=%s", tg_id)
            except Exception as exc:  # pragma: no cover - не должно случаться для свежего
                logger.warning("Failed to create default wallet for tg_id=%s: %s", tg_id, exc)

        return user

    async def get(self, tg_id: int) -> User | None:
        """Получить пользователя по tg_id."""
        result = await self._session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def set_tz(self, tg_id: int, tz: str) -> User | None:
        """
        Установить часовой пояс пользователю.

        Валидация ZoneInfo должна быть снаружи (в handler).

        Returns:
            Обновлённый User или None
        """
        from sqlalchemy import update

        result = await self._session.execute(
            update(User).where(User.tg_id == tg_id).values(tz=tz).returning(User)
        )
        user = result.scalar_one_or_none()
        if user:
            logger.info("TZ updated: tg_id=%s, tz=%s", tg_id, tz)
            await AuditLogRepository(self._session).record(
                actor_id=tg_id,
                actor_role="user",
                action=ACTION_SETTINGS_TZ,
                entity_type="user",
                entity_id=None,
            )
        return user

    async def set_notify_time(self, tg_id: int, notify_time: time) -> User | None:
        """
        Установить время уведомлений (notify_time) для пользователя.

        Используется в глобальных настройках (FR-10 / TASK-0026).

        Returns:
            Обновлённый User или None
        """
        from sqlalchemy import update

        result = await self._session.execute(
            update(User).where(User.tg_id == tg_id).values(notify_time=notify_time).returning(User)
        )
        user = result.scalar_one_or_none()
        if user:
            logger.info("notify_time updated: tg_id=%s, notify_time=%s", tg_id, notify_time)
            await AuditLogRepository(self._session).record(
                actor_id=tg_id,
                actor_role="user",
                action=ACTION_SETTINGS_NOTIFY_TIME,
                entity_type="user",
                entity_id=None,
            )
        return user

    async def set_global_days(self, tg_id: int, global_days: str) -> User | None:
        """
        Установить глобальные дни напоминаний (JSON-строка списка, напр. "[5,3,1]" или "[]").

        Валидация списка — в handler. Пустой = выключено.

        Returns:
            Обновлённый User или None
        """
        from sqlalchemy import update

        result = await self._session.execute(
            update(User).where(User.tg_id == tg_id).values(global_days=global_days).returning(User)
        )
        user = result.scalar_one_or_none()
        if user:
            logger.info("global_days updated: tg_id=%s, global_days=%s", tg_id, global_days)
            await AuditLogRepository(self._session).record(
                actor_id=tg_id,
                actor_role="user",
                action=ACTION_SETTINGS_DAYS,
                entity_type="user",
                entity_id=None,
            )
        return user
