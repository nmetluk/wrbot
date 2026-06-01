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


# M3 - Клавиатуры для создания списания (TASK-0011)


def get_charge_wallets_keyboard(wallets: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Выбор кошелька при создании списания + кнопка добавить новый."""
    builder = InlineKeyboardBuilder()
    for w in wallets:
        builder.add(
            InlineKeyboardButton(
                text=f"👛 {w['name']}",
                callback_data=f"charge_wallet_{w['id']}",
            )
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ Добавить новый кошелёк", callback_data="charge_add_wallet")
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_charge_categories_keyboard(categories: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Выбор категории или пропуск."""
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.add(
            InlineKeyboardButton(
                text=f"🏷️ {c['name']}",
                callback_data=f"charge_category_{c['id']}",
            )
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить категорию", callback_data="charge_skip_category")
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_charge_period_keyboard() -> InlineKeyboardMarkup:
    """Выбор периодичности."""
    builder = InlineKeyboardBuilder()
    periods = [
        ("Одноразово", "once"),
        ("Ежемесячно", "monthly"),
        ("Ежеквартально", "quarterly"),
        ("Ежегодно", "yearly"),
    ]
    for label, value in periods:
        builder.add(InlineKeyboardButton(text=label, callback_data=f"charge_period_{value}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_charge_notify_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа уведомлений."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🌍 Глобальные (по настройкам)",
            callback_data="charge_notify_global",
        )
    )
    builder.row(InlineKeyboardButton(text="✏️ Свои дни", callback_data="charge_notify_custom"))
    builder.row(InlineKeyboardButton(text="🚫 Отключить", callback_data="charge_notify_disable"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_charge_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение создания."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Создать списание", callback_data="charge_confirm_create"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой "Отмена" для пошаговых диалогов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )
