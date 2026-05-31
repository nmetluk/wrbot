"""
FSM states for multi-step dialogs.

Состояния для aiogram FSM — пошаговые диалоги создания/редактирования сущностей.
Будут заполнены в M2–M4.
"""

from aiogram.fsm.state import StatesGroup


class FormStates(StatesGroup):
    """Базовый класс для состояний форм."""

    pass


# TODO: M2 - добавить состояния для создания списания:
# class NewChargeStates(StatesGroup):
#     name = State()
#     amount = State()
#     wallet = State()
#     category = State()
#     next_date = State()
#     period = State()


# TODO: M2 - добавить состояния для создания кошелька:
# class NewWalletStates(StatesGroup):
#     name = State()


# TODO: M2 - добавить состояния для создания категории:
# class NewCategoryStates(StatesGroup):
#     name = State()


# TODO: M3 - добавить состояния для настроек:
# class SettingsStates(StatesGroup):
#     notify_time = State()
#     timezone = State()
#     global_days = State()
