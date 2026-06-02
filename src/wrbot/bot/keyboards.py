"""
Inline keyboards for bot UI.

Все клавиатуры собираются здесь — единое место для UI-логики.
"""

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Curated list of main Russian timezones for UI (per TASK-0025, not full IANA)
TZ_CHOICES: list[tuple[str, str]] = [
    ("Калининград (Europe/Kaliningrad) UTC+2", "Europe/Kaliningrad"),
    ("Москва (Europe/Moscow) UTC+3", "Europe/Moscow"),
    ("Самара (Europe/Samara) UTC+4", "Europe/Samara"),
    ("Екатеринбург (Asia/Yekaterinburg) UTC+5", "Asia/Yekaterinburg"),
    ("Омск (Asia/Omsk) UTC+6", "Asia/Omsk"),
    ("Красноярск (Asia/Krasnoyarsk) UTC+7", "Asia/Krasnoyarsk"),
    ("Иркутск (Asia/Irkutsk) UTC+8", "Asia/Irkutsk"),
    ("Якутск (Asia/Yakutsk) UTC+9", "Asia/Yakutsk"),
    ("Владивосток (Asia/Vladivostok) UTC+10", "Asia/Vladivostok"),
    ("Магадан (Asia/Magadan) UTC+11", "Asia/Magadan"),
    ("Камчатка (Asia/Kamchatka) UTC+12", "Asia/Kamchatka"),
]


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
    builder.row(InlineKeyboardButton(text="🕒 Часовой пояс", callback_data="settings_tz"))
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


# M3 - Клавиатуры для списка и действий над списаниями (TASK-0012)


def get_my_charges_keyboard(charges: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Список активных списаний с кнопками на карточку."""
    builder = InlineKeyboardBuilder()
    for ch in charges:
        text = f"{ch['name']} — {ch.get('amount', '?')} ₽ — {ch.get('next_date', '?')}"
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"charge_item_{ch['id']}",
            )
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="➕ Новое списание", callback_data="new_charge"))
    builder.row(InlineKeyboardButton(text="◀️ В меню", callback_data="main_menu"))
    builder.row(InlineKeyboardButton(text="❌ Закрыть", callback_data="cancel"))
    return builder.as_markup()


def get_charge_card_actions_keyboard(charge_id: int) -> InlineKeyboardMarkup:
    """Карточка списания с действиями."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"charge_edit_{charge_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"charge_delete_{charge_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Отметить оплаченным",
            callback_data=f"charge_paid_{charge_id}",
        ),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад к списку", callback_data="list_charges"))
    return builder.as_markup()


def get_my_charges_empty_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустого списка «Мои списания» — навигация (TASK-0036)."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Новое списание", callback_data="new_charge"))
    builder.row(InlineKeyboardButton(text="◀️ В меню", callback_data="main_menu"))
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой "Отмена" для пошаговых диалогов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )


# M4 - Клавиатура для кнопок в уведомлении-напоминании (TASK-0015)
# Используется при отправке (TASK-0016), но определена здесь для централизации UI.


def get_reminder_actions_keyboard(charge_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий из push-уведомления: Оплачено / Отложить / Редактировать.

    Callbacks специфичны (remind_*) — защищает роутинг (урок TASK-0008).
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Оплачено", callback_data=f"remind_paid_{charge_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="⏰ Отложить", callback_data=f"remind_snooze_{charge_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"remind_edit_{charge_id}"),
    )
    return builder.as_markup()


def get_tz_keyboard(current_tz: str) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора часового пояса.

    Показывает текущий с пометкой, кнопки для каждого из курируемого списка.
    Callbacks специфичны tz_set_<iana_replaced> — не перехватывают чужие (урок TASK-0008).

    Args:
        current_tz: текущий IANA tz пользователя

    Returns:
        InlineKeyboardMarkup с выбором TZ
    """
    builder = InlineKeyboardBuilder()

    for display, iana in TZ_CHOICES:
        prefix = "✅ " if iana == current_tz else ""
        # Replace / with _ for safe callback_data
        cb_data = f"tz_set_{iana.replace('/', '_')}"
        builder.row(InlineKeyboardButton(text=f"{prefix}{display}", callback_data=cb_data))

    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings"))
    return builder.as_markup()


# TASK-0026: клавиатуры для глобальных уведомлений (FR-10)


def get_global_notify_keyboard(notify_time: str, global_days: list[int]) -> InlineKeyboardMarkup:
    """
    Экран «Глобальные уведомления»: показывает текущие значения и кнопки редактирования.

    Callbacks: gnotify_time, gnotify_days — специфичные (не перехватываются).

    Args:
        notify_time: строка "ЧЧ:ММ"
        global_days: список дней, [] = выключено

    Returns:
        Клавиатура с текущим статусом и действиями.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🕒 Изменить время", callback_data="gnotify_time"),
        InlineKeyboardButton(text="📆 Изменить дни", callback_data="gnotify_days"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="settings"))
    return builder.as_markup()


def get_global_days_edit_keyboard(selected: list[int]) -> InlineKeyboardMarkup:
    """
    Экран редактирования дней с переключателями (toggle) и сохранением.

    Использует специфичные callback'и gday_toggle_<n> (урок TASK-0008 — не ловятся broad).
    Поддерживает комбинации 5/3/1 и произвольные (через «Ввести вручную»).

    Args:
        selected: текущий выбранный список дней

    Returns:
        InlineKeyboard с кнопками дней и управлением.
    """
    COMMON_DAYS = [1, 2, 3, 5, 7, 10, 14, 21, 30]
    builder = InlineKeyboardBuilder()

    # Кнопки toggle в 3 колонки
    row: list[InlineKeyboardButton] = []
    for d in COMMON_DAYS:
        prefix = "✅ " if d in selected else "⬜ "
        row.append(InlineKeyboardButton(text=f"{prefix}{d}", callback_data=f"gday_toggle_{d}"))
        if len(row) == 3:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="gdays_save"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    builder.row(InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="gdays_input"))
    return builder.as_markup()
