"""
Сервисы для работы со справочными данными.

Валидация, проверка лимитов, доменные ошибки.
"""

import logging
from typing import NewType

from wrbot.config import get_settings

logger = logging.getLogger(__name__)

# Типы для доменных ошибок
WalletName = NewType("WalletName", str)
CategoryName = NewType("CategoryName", str)


class ReferenceError(Exception):
    """Базовое исключение для операций со справочниками."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class LimitExceeded(ReferenceError):
    """Превышен лимит на число объектов."""


class DuplicateName(ReferenceError):
    """Объект с таким именем уже существует."""


class InvalidName(ReferenceError):
    """Недопустимое имя."""


def validate_and_trim_name(raw: str, max_length: int = 100) -> str:
    """
    Валидировать и нормализовать имя кошелька/категории.

    - Обрезает пробелы по краям
    - Проверяет на пустоту
    - Проверяет длину

    Args:
        raw: Сырое имя от пользователя
        max_length: Максимальная длина

    Returns:
        Нормализованное имя

    Raises:
        InvalidName: если имя пустое или слишком длинное
    """
    trimmed = raw.strip()
    if not trimmed:
        raise InvalidName("Имя не может быть пустым")
    if len(trimmed) > max_length:
        raise InvalidName(f"Имя слишком длинное (максимум {max_length} символов)")
    return trimmed


def check_wallet_limit(current_count: int) -> None:
    """
    Проверить лимит кошельков.

    Args:
        current_count: Текущее число кошельков пользователя

    Raises:
        LimitExceeded: если лимит превышен
    """
    settings = get_settings()
    if current_count >= settings.max_wallets:
        raise LimitExceeded(f"Превышен лимит кошельков (максимум {settings.max_wallets})")


def check_category_limit(current_count: int) -> None:
    """
    Проверить лимит категорий.

    Args:
        current_count: Текущее число категорий пользователя

    Raises:
        LimitExceeded: если лимит превышен
    """
    settings = get_settings()
    if current_count >= settings.max_categories:
        raise LimitExceeded(f"Превышен лимит категорий (максимум {settings.max_categories})")
