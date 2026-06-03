"""
FSM states for multi-step dialogs.

Состояния для aiogram FSM — пошаговые диалоги создания/редактирования сущностей.
"""

from aiogram.fsm.state import State, StatesGroup


class FormStates(StatesGroup):
    """Базовый класс для состояний форм."""

    pass


# M2 - состояния для кошельков
class WalletStates(StatesGroup):
    """Состояния для создания/переименования кошелька."""

    name = State()  # Ввод названия кошелька


# M2 - состояния для категорий
class CategoryStates(StatesGroup):
    """Состояния для создания/переименования категории."""

    name = State()  # Ввод названия категории


# M2 - состояние подтверждения удаления
class ConfirmDeleteStates(StatesGroup):
    """Состояние для подтверждения удаления."""

    confirm = State()  # Ожидание подтверждения


# M3 - состояния для создания списания (TASK-0011)
class NewChargeStates(StatesGroup):
    """Состояния пошагового создания списания."""

    name = State()  # 1. Название
    amount = State()  # 2. Сумма
    wallet = State()  # 3. Кошелёк (выбор + возможность добавить новый)
    category = State()  # 4. Категория (или пропустить)
    period = State()  # 5. Периодичность (сначала период, затем дата — TASK-0040)
    next_date = State()  # 6. Дата следующего списания (ДД.ММ.ГГГГ)
    notify = State()  # 7. Уведомления (глобальные / свои дни / отключить)


# M5 / TASK-0026 - состояния для глобальных уведомлений (FR-10)
class SettingsStates(StatesGroup):
    """Состояния для редактирования настроек глобальных уведомлений: время и дни."""

    notify_time = State()  # Ввод времени ЧЧ:ММ
    global_days = State()  # Редактирование дней (toggle или ввод)
