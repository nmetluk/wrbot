"""
Start handler and main menu.

Обрабатывает команду /start и показывает главное меню.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Обработчик команды /cancel — отменяет текущий диалог."""
    # TODO: M2 - сбросить FSM состояние пользователя
    await message.answer(Texts.action_cancelled)
