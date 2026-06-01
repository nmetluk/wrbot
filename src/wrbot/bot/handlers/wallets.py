"""Wallets handlers — CRUD operations."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from wrbot.bot.keyboards import (
    get_cancel_keyboard,
    get_confirm_delete_keyboard,
    get_wallet_actions_keyboard,
    get_wallets_keyboard,
)
from wrbot.bot.states import WalletStates
from wrbot.bot.texts import Texts
from wrbot.repositories.wallets import WalletRepository
from wrbot.services.reference import DuplicateName, InvalidName, LimitExceeded, ReferenceError

logger = logging.getLogger(__name__)

router = Router(name="wallets")


@router.callback_query(F.data.startswith("wallet_"))
async def wallet_details(callback: CallbackQuery) -> None:
    """Показать детали кошелька с действиями."""
    wallet_id = int(callback.data.split("_")[1])
    keyboard = get_wallet_actions_keyboard(wallet_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "wallet_add")
async def wallet_add_start(callback: CallbackQuery, state: FSMContext, **data: dict) -> None:
    """Начать добавление кошелька."""
    session = data["session"]
    await state.update_data(session=session, wallet_id=None)
    await state.set_state(WalletStates.name)
    await callback.message.edit_text(Texts.wallet_enter_name, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("wallet_rename_"))
async def wallet_rename_start(
    callback: CallbackQuery, state: FSMContext, **handler_data: dict
) -> None:
    """Начать переименование кошелька."""
    wallet_id = int(callback.data.split("_")[2])
    session = handler_data["session"]
    await state.update_data(session=session, wallet_id=wallet_id)

    await state.set_state(WalletStates.name)

    # Получаем текущее название
    repo = WalletRepository(session)
    wallet = await repo.get(callback.from_user.id, wallet_id)
    wallet_name = wallet.name if wallet else "?"

    await callback.message.edit_text(
        Texts.wallet_enter_new_name.format(name=wallet_name), reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wallet_delete_"))
async def wallet_delete_confirm(
    callback: CallbackQuery, state: FSMContext, **handler_data: dict
) -> None:
    """Показать подтверждение удаления кошелька."""
    wallet_id = int(callback.data.split("_")[2])
    session = handler_data["session"]

    repo = WalletRepository(session)
    wallet = await repo.get(callback.from_user.id, wallet_id)

    if wallet:
        await state.update_data(wallet_id=wallet_id)
        keyboard = get_confirm_delete_keyboard("wallet", wallet_id)
        await callback.message.edit_text(
            Texts.wallet_confirm_delete.format(name=wallet.name), reply_markup=keyboard
        )

    await callback.answer()


@router.callback_query(F.data.startswith("wallet_confirm_"))
async def wallet_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """Удалить кошелёк."""
    state_data = await state.get_data()
    wallet_id = state_data.get("wallet_id")
    session = state_data.get("session")

    if not wallet_id or not session:
        await callback.answer(Texts.error_generic, show_alert=True)
        return

    repo = WalletRepository(session)
    tg_id = callback.from_user.id

    deleted = await repo.delete(tg_id, wallet_id)

    if deleted:
        await callback.message.edit_text(Texts.wallet_deleted.format(name="?"))

        # Показать обновлённый список
        wallets = await repo.list_by_user(tg_id)
        wallet_data = [{"id": w.id, "name": w.name} for w in wallets]
        keyboard = get_wallets_keyboard(wallet_data)

        lines = [Texts.wallet_list_item.format(name=w["name"]) for w in wallet_data]
        text = "👛 *Кошельки/карты*\n\n" + "\n".join(lines)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.answer(Texts.error_not_found, show_alert=True)

    await state.clear()


@router.message(WalletStates.name)
async def wallet_name_handler(message: Message, state: FSMContext) -> None:
    """Обработать ввод названия кошелька (добавление или переименование)."""
    state_data = await state.get_data()
    session = state_data.get("session")
    wallet_id = state_data.get("wallet_id")

    if not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    wallet_repo = WalletRepository(session)
    tg_id = message.from_user.id

    try:
        if wallet_id is None:
            # Добавление нового кошелька
            wallet = await wallet_repo.create(tg_id, message.text or "")
            await message.answer(Texts.wallet_added.format(name=wallet.name))
        else:
            # Переименование существующего
            wallet = await wallet_repo.rename(tg_id, wallet_id, message.text or "")
            if wallet:
                await message.answer(Texts.wallet_renamed.format(name=wallet.name))
            else:
                await message.answer(Texts.error_not_found)
                await state.clear()
                return

        # Показать обновлённый список
        wallets = await wallet_repo.list_by_user(tg_id)
        wallet_data = [{"id": w.id, "name": w.name} for w in wallets]
        keyboard = get_wallets_keyboard(wallet_data)

        lines = [Texts.wallet_list_item.format(name=w["name"]) for w in wallet_data]
        text = "👛 *Кошельки/карты*\n\n" + "\n".join(lines)
        await message.answer(text, reply_markup=keyboard)

    except InvalidName as e:
        if "пуст" in str(e):
            await message.answer(Texts.error_empty_name)
        else:
            settings = __import__("wrbot.config").config.get_settings()
            await message.answer(Texts.error_name_too_long.format(max=100))
    except LimitExceeded:
        settings = __import__("wrbot.config").config.get_settings()
        await message.answer(Texts.error_limit_exceeded.format(max=settings.max_wallets))
    except DuplicateName:
        await message.answer(Texts.error_duplicate_name)
    except ReferenceError as e:
        logger.error("Wallet error: %s", e)
        await message.answer(Texts.error_generic)

    await state.clear()
