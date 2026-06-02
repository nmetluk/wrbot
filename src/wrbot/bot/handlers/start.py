"""
Start handler and main menu.

Обрабатывает команду /start, показывает главное меню и callbacks главного меню.
Для новых пользователей (TASK-0035) — онбординг: упоминание созданного дефолтного
кошелька + подсказка про настройки кошельков/категорий.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command

from wrbot.bot.keyboards import get_main_menu_keyboard
from wrbot.bot.texts import Texts
from wrbot.repositories.users import UserRepository

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, Message
    from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Обработчик команды /start — показывает главное меню + онбординг для новых."""
    user_repo = UserRepository(session)
    existing = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
    await user_repo.get_or_create(message.from_user.id)  # type: ignore[union-attr]  # side-effect: default wallet if new

    is_new = existing is None
    if is_new:
        text = (
            Texts.start_greeting
            + "\n\n"
            + Texts.start_new_user_wallet_created
            + "\n\n"
            + Texts.start_onboarding_hint
        )
    else:
        text = Texts.start_greeting + "\n\n" + Texts.start_onboarding_hint

    await message.answer(
        text,
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
