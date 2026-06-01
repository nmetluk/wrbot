"""
Start handler and main menu.

Обрабатывает команду /start, показывает главное меню и callbacks главного меню.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from wrbot.bot.keyboards import get_main_menu_keyboard
from wrbot.bot.texts import Texts

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start — показывает главное меню."""
    await message.answer(
        Texts.start_greeting,
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help — показывает справку."""
    await message.answer(Texts.help_text)


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    """Обработчик кнопки «❔ Помощь» — показывает справку."""
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.help_text, reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


# Обработчик "new_charge" теперь в charges_create_handler (TASK-0011)
# Заглушка удалена, чтобы не конфликтовать.


# Обработчик "list_charges" теперь в charges_list_handler (TASK-0012)
# Заглушка удалена.


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Обработчик команды /cancel — отменяет текущий диалог."""
    await state.clear()
    await message.answer(Texts.action_cancelled)
