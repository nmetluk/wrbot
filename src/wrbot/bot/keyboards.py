"""
Inline keyboards for bot UI.

Все клавиатуры собираются здесь — единое место для UI-логики.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой "Отмена" для пошаговых диалогов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )
