"""
Category repository.

Доступ к данным категорий с изоляцией по user_id (FR-13).
"""

import json
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import Category
from wrbot.repositories.audit_log import (
    ACTION_CATEGORY_CREATE,
    ACTION_CATEGORY_DELETE,
    ACTION_CATEGORY_NOTIFY_ADD,
    ACTION_CATEGORY_NOTIFY_REMOVE,
    ACTION_CATEGORY_RENAME,
    AuditLogRepository,
)
from wrbot.services.reference import (
    DuplicateName,
    check_category_limit,
    validate_and_trim_name,
)

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Репозиторий для работы с категориями."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.

        Args:
            session: Сессия БД SQLAlchemy
        """
        self._session = session

    async def create(self, user_id: int, name: str) -> Category:
        """
        Создать новую категорию для пользователя.

        Args:
            user_id: ID пользователя (tg_id)
            name: Название категории

        Returns:
            Созданная категория

        Raises:
            InvalidName: если имя некорректно
            LimitExceeded: если превышен лимит категорий
            DuplicateName: если имя уже занято
        """
        # Валидация имени
        validated_name = validate_and_trim_name(name)

        # Проверка лимита
        result = await self._session.execute(select(Category.id).where(Category.user_id == user_id))
        count = len(result.all())
        check_category_limit(count)

        # Проверка на дубликат имени
        existing = await self._session.execute(
            select(Category).where(Category.user_id == user_id, Category.name == validated_name)
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateName(f"Категория «{validated_name}» уже существует")

        # Создание
        category = Category(user_id=user_id, name=validated_name)
        self._session.add(category)
        await self._session.flush()
        logger.info("Created category: user_id=%s, name=%s", user_id, validated_name)
        await AuditLogRepository(self._session).record(
            actor_id=user_id,
            actor_role="user",
            action=ACTION_CATEGORY_CREATE,
            entity_type="category",
            entity_id=category.id,
        )
        return category

    async def list_by_user(self, user_id: int) -> list[Category]:
        """
        Получить список категорий пользователя.

        Отсортирован по имени, затем по ID.

        Args:
            user_id: ID пользователя (tg_id)

        Returns:
            Список категорий (может быть пустым)
        """
        result = await self._session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name, Category.id)
        )
        return list(result.scalars().all())

    async def get(self, user_id: int, category_id: int) -> Category | None:
        """
        Получить категорию по ID с проверкой владельца.

        Args:
            user_id: ID пользователя (tg_id)
            category_id: ID категории

        Returns:
            Категория или None, если не найдена или не принадлежит пользователю
        """
        result = await self._session.execute(
            select(Category).where(Category.user_id == user_id, Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def rename(self, user_id: int, category_id: int, new_name: str) -> Category | None:
        """
        Переименовать категорию.

        Args:
            user_id: ID пользователя (tg_id)
            category_id: ID категории
            new_name: Новое название

        Returns:
            Обновлённая категория или None, если не найдена

        Raises:
            InvalidName: если имя некорректно
            DuplicateName: если новое имя уже занято другой категорией
        """
        validated_name = validate_and_trim_name(new_name)

        # Проверка на дубликат имени (кроме текущего)
        existing = await self._session.execute(
            select(Category).where(
                Category.user_id == user_id,
                Category.name == validated_name,
                Category.id != category_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateName(f"Категория «{validated_name}» уже существует")

        # Обновление
        result = await self._session.execute(
            update(Category)
            .where(Category.user_id == user_id, Category.id == category_id)
            .values(name=validated_name)
            .returning(Category)
        )
        category = result.scalar_one_or_none()
        if category:
            logger.info(
                "Renamed category: user_id=%s, category_id=%s, new_name=%s",
                user_id,
                category_id,
                validated_name,
            )
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CATEGORY_RENAME,
                entity_type="category",
                entity_id=category_id,
            )
        return category

    async def delete(self, user_id: int, category_id: int) -> bool:
        """
        Удалить категорию.

        Args:
            user_id: ID пользователя (tg_id)
            category_id: ID категории

        Returns:
            True если удалена, False если не найдена
        """
        result = await self._session.execute(
            delete(Category).where(Category.user_id == user_id, Category.id == category_id)
        )
        deleted: bool = result.rowcount > 0  # type: ignore[attr-defined]
        if deleted:
            logger.info("Deleted category: user_id=%s, category_id=%s", user_id, category_id)
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CATEGORY_DELETE,
                entity_type="category",
                entity_id=category_id,
            )
        return deleted

    async def get_notify_chat_ids(self, user_id: int, category_id: int) -> list[int]:
        """Получить список chat_id целей для дубля напоминаний (TASK-0043)."""
        cat = await self.get(user_id, category_id)
        if not cat or not cat.notify_chat_ids:
            return []
        try:
            val = json.loads(cat.notify_chat_ids)
            if isinstance(val, list):
                return [int(x) for x in val if str(x).strip()]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return []

    async def add_notify_chat_id(self, user_id: int, category_id: int, chat_id: int) -> bool:
        """
        Добавить chat_id цели (идемпотентно, дедуп). Сериализация JSON.
        Возвращает True если добавлено/изменено.
        """
        cat = await self.get(user_id, category_id)
        if not cat:
            return False
        current = await self.get_notify_chat_ids(user_id, category_id)
        if chat_id in current:
            return False  # уже есть
        current.append(chat_id)
        new_val = json.dumps(sorted(set(current)))
        result = await self._session.execute(
            update(Category)
            .where(Category.user_id == user_id, Category.id == category_id)
            .values(notify_chat_ids=new_val)
            .returning(Category)
        )
        updated = result.scalar_one_or_none()
        if updated:
            logger.info(
                "Added notify chat_id %s for category %s (user %s)",
                chat_id,
                category_id,
                user_id,
            )
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CATEGORY_NOTIFY_ADD,
                entity_type="category",
                entity_id=category_id,
            )
        return bool(updated)

    async def remove_notify_chat_id(self, user_id: int, category_id: int, chat_id: int) -> bool:
        """Удалить chat_id цели. Если список пуст — ставит NULL."""
        cat = await self.get(user_id, category_id)
        if not cat:
            return False
        current = await self.get_notify_chat_ids(user_id, category_id)
        if chat_id not in current:
            return False
        current = [c for c in current if c != chat_id]
        new_val = json.dumps(sorted(current)) if current else None
        result = await self._session.execute(
            update(Category)
            .where(Category.user_id == user_id, Category.id == category_id)
            .values(notify_chat_ids=new_val)
            .returning(Category)
        )
        updated = result.scalar_one_or_none()
        if updated:
            logger.info(
                "Removed notify chat_id %s for category %s (user %s)",
                chat_id,
                category_id,
                user_id,
            )
            await AuditLogRepository(self._session).record(
                actor_id=user_id,
                actor_role="user",
                action=ACTION_CATEGORY_NOTIFY_REMOVE,
                entity_type="category",
                entity_id=category_id,
            )
        return bool(updated)
