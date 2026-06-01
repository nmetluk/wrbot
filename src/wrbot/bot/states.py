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


# TODO: M3 - добавить состояния для создания списания:
# class NewChargeStates(StatesGroup):
#     name = State()
#     amount = State()
#     wallet = State()
#     category = State()
#     next_date = State()
#     period = State()


# TODO: M3 - добавить состояния для настроек:
# class SettingsStates(StatesGroup):
#     notify_time = State()
#     timezone = State()
#     global_days = State()
