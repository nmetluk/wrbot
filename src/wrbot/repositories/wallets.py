"""
Wallet repository.

Доступ к данным кошельков с изоляцией по user_id (FR-13).
"""

import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import Wallet
from wrbot.repositories.audit_log import (
    ACTION_WALLET_CREATE,
    ACTION_WALLET_DELETE,
    ACTION_WALLET_RENAME,
    AuditLogRepository,
)
from wrbot.services.reference import (
    DuplicateName,
    check_wallet_limit,
    validate_and_trim_name,
)

logger = logging.getLogger(__name__)


class WalletRepository:
    """Репозиторий для работы с кошельками."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.

        Args:
            session: Сессия БД SQLAlchemy
        """
        self._session = session

    async def create(self, user_id: int, name: str) -> Wallet:
        """
        Создать новый кошелёк для пользователя.

        Args:
            user_id: ID пользователя (tg_id)
            name: Название кошелька

        Returns:
            Созданный кошелёк

        Raises:
            InvalidName: если имя некорректно
            LimitExceeded: если превышен лимит кошельков
            DuplicateName: если имя уже занято
        """
        # Валидация имени
        validated_name = validate_and_trim_name(name)

        # Проверка лимита
        result = await self._session.execute(select(Wallet.id).where(Wallet.user_id == user_id))
        count = len(result.all())
        check_wallet_limit(count)

        # Проверка на дубликат имени
        existing = await self._session.execute(
            select(Wallet).where(Wallet.user_id == user_id, Wallet.name == validated_name)
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateName(f"Кошелёк «{validated_name}» уже существует")

        # Создание
        wallet = Wallet(user_id=user_id, name=validated_name)
        self._session.add(wallet)
        await self._session.flush()
        logger.info("Created wallet: user_id=%s, name=%s", user_id, validated_name)
        await AuditLogRepository(self._session).record(
            actor_id=user_id,
            actor_role="user",
            action=ACTION_WALLET_CREATE,
            entity_type="wallet",
            entity_id=wallet.id,
        )
        return wallet

    async def list_by_user(self, user_id: int) -> list[Wallet]:
        """
        Получить список кошельков пользователя.

        Отсортирован по имени, затем по ID.

        Args:
            user_id: ID пользователя (tg_id)

        Returns:
            Список кошельков (может быть пустым)
        """
        result = await self._session.execute(
            select(Wallet).where(Wallet.user_id == user_id).order_by(Wallet.name, Wallet.id)
        )
        return list(result.scalars().all())

    async def get(self, user_id: int, wallet_id: int) -> Wallet | None:
        """
        Получить кошелёк по ID с проверкой владельца.

        Args:
            user_id: ID пользователя (tg_id)
            wallet_id: ID кошелька

        Returns:
            Кошелёк или None, если не найден или не принадлежит пользователю
        """
        result = await self._session.execute(
            select(Wallet).where(Wallet.user_id == user_id, Wallet.id == wallet_id)
        )
        return result.scalar_one_or_none()

    async def rename(self, user_id: int, wallet_id: int, new_name: str) -> Wallet | None:
        """
        Переименовать кошелёк.

        Args:
            user_id: ID пользователя (tg_id)
            wallet_id: ID кошелька
            new_name: Новое название

        Returns:
            Обновлённый кошелёк или None, если не найден

        Raises:
            InvalidName: если имя некорректно
            DuplicateName: если новое имя уже занято другим кошельком
        """
        validated_name = validate_and_trim_name(new_name)

        # Проверка на дубликат имени (кроме текущего)
        existing = await self._session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.name == validated_name,
                Wallet.id != wallet_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateName(f"Кошелёк «{validated_name}» уже существует")

        # Обновление
        result = await self._session.execute(
            update(Wallet)
            .where(Wallet.user_id == user_id, Wallet.id == wallet_id)
            .values(name=validated_name)
            .returning(Wallet)
        )
        wallet = result.scalar_one_or_none()
        if wallet:
            logger.info(
                "Renamed wallet: user_id=%s, wallet_id=%s, new_name=%s",
                user_id,
                wallet_id,
                validated_name,
            )
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_WALLET_RENAME,
                entity_type="wallet",
                entity_id=wallet_id,
            )
        return wallet

    async def delete(self, user_id: int, wallet_id: int) -> bool:
        """
        Удалить кошелёк.

        Args:
            user_id: ID пользователя (tg_id)
            wallet_id: ID кошелька

        Returns:
            True если удалён, False если не найден
        """
        result = await self._session.execute(
            delete(Wallet).where(Wallet.user_id == user_id, Wallet.id == wallet_id)
        )
        deleted: bool = result.rowcount > 0  # type: ignore[attr-defined]
        if deleted:
            logger.info("Deleted wallet: user_id=%s, wallet_id=%s", user_id, wallet_id)
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_WALLET_DELETE,
                entity_type="wallet",
                entity_id=wallet_id,
            )
        return deleted
