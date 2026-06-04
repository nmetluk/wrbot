"""
AuditLog repository (M6, TASK-0032, ADR-0010).

Запись действий без чувствительных данных.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import AuditLog

logger = logging.getLogger(__name__)

# Константы типов действий (как строки, для простоты и тестов)
ACTION_CHARGE_CREATE = "charge.create"
ACTION_CHARGE_EDIT = "charge.edit"
ACTION_CHARGE_DELETE = "charge.delete"
ACTION_CHARGE_PAID = "charge.paid"
ACTION_CHARGE_SNOOZE = "charge.snooze"
ACTION_WALLET_CREATE = "wallet.create"
ACTION_WALLET_RENAME = "wallet.rename"
ACTION_WALLET_DELETE = "wallet.delete"
ACTION_WALLET_SET_ICON = "wallet.set_icon"
ACTION_CATEGORY_CREATE = "category.create"
ACTION_CATEGORY_RENAME = "category.rename"
ACTION_CATEGORY_DELETE = "category.delete"
ACTION_CATEGORY_NOTIFY_ADD = "category.notify.add"
ACTION_CATEGORY_NOTIFY_REMOVE = "category.notify.remove"
ACTION_SETTINGS_NOTIFY_TIME = "settings.notify_time"
ACTION_SETTINGS_DAYS = "settings.days"
ACTION_SETTINGS_TZ = "settings.tz"
ACTION_REMINDER_SENT = "reminder.sent"
ACTION_ERROR = "error.critical"


class AuditLogRepository:
    """Репозиторий для аудита действий."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        actor_id: int,
        actor_role: str,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> AuditLog:
        """
        Записать действие в аудит-лог.

        Args:
            actor_id: tg_id актёра (или 0 для system)
            actor_role: 'user' | 'admin' | 'system'
            action: тип действия (e.g. 'charge.create', 'settings.tz')
            entity_type: 'charge' | 'wallet' | 'category' | None
            entity_id: id сущности или None

        Returns:
            Созданная запись AuditLog
        """
        log_entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            created_at=datetime.now(),
        )
        self._session.add(log_entry)
        await self._session.flush()
        logger.info(
            "Audit log: actor=%s(%s) action=%s entity=%s:%s",
            actor_id,
            actor_role,
            action,
            entity_type,
            entity_id,
        )
        return log_entry

    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        """Список недавних записей (для дашборда/админа)."""
        result = await self._session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
