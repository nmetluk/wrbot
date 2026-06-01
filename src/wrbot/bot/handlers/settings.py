"""Settings menu handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aiogram import F, Router
from aiogram.filters import Command

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, Message
    from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.bot.keyboards import (
    get_categories_keyboard,
    get_settings_menu_keyboard,
    get_wallets_keyboard,
)
from wrbot.bot.texts import Texts
from wrbot.repositories.categories import CategoryRepository
from wrbot.repositories.users import UserRepository
from wrbot.repositories.wallets import WalletRepository

logger = logging.getLogger(__name__)

router = Router(name="settings")


@router.callback_query(F.data == "settings")
async def settings_menu(callback: CallbackQuery) -> None:
    """Показать меню настроек."""
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.settings_menu, reply_markup=get_settings_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery) -> None:
    """Вернуться в главное меню."""
    from wrbot.bot.keyboards import get_main_menu_keyboard

    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.start_greeting, reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings_global")
async def global_settings_stub(callback: CallbackQuery) -> None:
    """Заглушка для глобальных уведомлений (M3)."""
    await callback.answer(Texts.global_settings_stub, show_alert=True)


@router.callback_query(F.data == "settings_wallets")
async def wallets_list(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Показать список кошельков."""
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    wallet_repo = WalletRepository(session)

    # Upsert пользователя
    tg_id = callback.from_user.id
    await user_repo.get_or_create(tg_id)

    # Получаем кошельки
    wallets = await wallet_repo.list_by_user(tg_id)
    wallet_data = [{"id": w.id, "name": w.name} for w in wallets]

    if not wallet_data:
        text = Texts.wallets_list_empty
        keyboard = get_wallets_keyboard([])
    else:
        lines = [Texts.wallet_list_item.format(name=w["name"]) for w in wallet_data]
        text = "👛 *Кошельки/карты*\n\n" + "\n".join(lines)
        keyboard = get_wallets_keyboard(wallet_data)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "settings_categories")
async def categories_list(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Показать список категорий."""
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    category_repo = CategoryRepository(session)

    # Upsert пользователя
    tg_id = callback.from_user.id
    await user_repo.get_or_create(tg_id)

    # Получаем категории
    categories = await category_repo.list_by_user(tg_id)
    category_data = [{"id": c.id, "name": c.name} for c in categories]

    if not category_data:
        text = Texts.categories_list_empty
        keyboard = get_categories_keyboard([])
    else:
        lines = [Texts.category_list_item.format(name=c["name"]) for c in category_data]
        text = "🏷️ *Категории*\n\n" + "\n".join(lines)
        keyboard = get_categories_keyboard(category_data)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Отменить текущее действие."""
    await state.clear()
    await callback.message.edit_text(Texts.action_cancelled)  # type: ignore[union-attr]
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    """Отменить текущее действие (команда)."""
    await state.clear()
    await message.answer(Texts.action_cancelled)
