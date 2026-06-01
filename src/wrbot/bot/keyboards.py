"""
Inline keyboards for bot UI.

Все клавиатуры собираются здесь — единое место для UI-логики.
"""

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню бота.

    Кнопки:
    - ➕ Новое списание
    - 📋 Мои списания
    - ⚙️ Настройки
    - ❔ Помощь
    """
    buttons = [
        [
            InlineKeyboardButton(text="➕ Новое списание", callback_data="new_charge"),
        ],
        [
            InlineKeyboardButton(text="📋 Мои списания", callback_data="list_charges"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="❔ Помощь", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Меню настроек.

    Кнопки:
    - 👛 Кошельки/карты
    - 🏷️ Категории
    - 🔔 Глобальные уведомления (заглушка M3)
    - ◀️ Назад
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👛 Кошельки/карты", callback_data="settings_wallets"),
        InlineKeyboardButton(text="🏷️ Категории", callback_data="settings_categories"),
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Глобальные уведомления", callback_data="settings_global")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_wallets_keyboard(wallets: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Клавиатура списка кошельков.

    Args:
        wallets: Список кошельков с полями id, name

    Returns:
        Клавиатура с кошельками и кнопками управления
    """
    builder = InlineKeyboardBuilder()

    # Кнопки кошельков
    for wallet in wallets:
        # Кнопка с названием кошелька
        builder.add(
            InlineKeyboardButton(
                text=f"👛 {wallet['name']}",
                callback_data=f"wallet_item_{wallet['id']}",
            )
        )

    # Разбиваем на 2 колонки
    builder.adjust(2)

    # Кнопки управления
    builder.row(InlineKeyboardButton(text="➕ Добавить", callback_data="wallet_add"))
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    )

    return builder.as_markup()


def get_wallet_actions_keyboard(wallet_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура действий над кошельком.

    Args:
        wallet_id: ID кошелька

    Returns:
        Клавиатура с кнопками действий
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"wallet_rename_{wallet_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"wallet_delete_{wallet_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings_wallets"))
    return builder.as_markup()


def get_categories_keyboard(categories: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Клавиатура списка категорий.

    Args:
        categories: Список категорий с полями id, name

    Returns:
        Клавиатура с категориями и кнопками управления
    """
    builder = InlineKeyboardBuilder()

    # Кнопки категорий
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=f"🏷️ {category['name']}",
                callback_data=f"category_item_{category['id']}",
            )
        )

    # Разбиваем на 2 колонки
    builder.adjust(2)

    # Кнопки управления
    builder.row(InlineKeyboardButton(text="➕ Добавить", callback_data="category_add"))
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    )

    return builder.as_markup()


def get_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура действий над категорией.

    Args:
        category_id: ID категории

    Returns:
        Клавиатура с кнопками действий
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Переименовать", callback_data=f"category_rename_{category_id}"
        ),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"category_delete_{category_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings_categories"))
    return builder.as_markup()


def get_confirm_delete_keyboard(entity_type: str, entity_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения удаления.

    Args:
        entity_type: Тип сущности (wallet или category)
        entity_id: ID сущности

    Returns:
        Клавиатура с кнопками подтверждения
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"{entity_type}_confirm_{entity_id}",
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой "Отмена" для пошаговых диалогов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )
