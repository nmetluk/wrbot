"""
Handlers for charge list and actions (M3, TASK-0012).

List, card, edit (reuses FSM), delete, paid. Specific callbacks + router test.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

from wrbot.bot.keyboards import (
    get_charge_card_actions_keyboard,
    get_confirm_delete_keyboard,
    get_main_menu_keyboard,
    get_my_charges_empty_keyboard,
    get_my_charges_keyboard,
)
from wrbot.bot.texts import Texts
from wrbot.repositories.charges import ChargeRepository
from wrbot.repositories.users import UserRepository
from wrbot.services.formatters import (
    build_charge_card_text,
    format_date_ru,
    resolve_wallet_name,
)

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = Router(name="charges_list")


@router.callback_query(F.data == "list_charges")
async def list_charges(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Show list of active charges for the user."""
    await state.clear()  # clean any previous FSM

    user_repo = UserRepository(session)
    user = await user_repo.get_or_create(callback.from_user.id)

    charge_repo = ChargeRepository(session)
    charges = await charge_repo.list_active_by_user(user.tg_id)

    if not charges:
        kb = get_my_charges_empty_keyboard()
        await callback.message.edit_text(Texts.my_charges_empty, reply_markup=kb)  # type: ignore[union-attr]
        await callback.answer()
        return

    # Резолв имён кошельков через общий форматтер + ДД.ММ (TASK-0039, избегаем дублирования resolve)
    charge_data = []
    for c in charges:
        wname = await resolve_wallet_name(session, user.tg_id, c.wallet_id)
        dstr = format_date_ru(c.next_date)
        charge_data.append(
            {
                "id": c.id,
                "name": c.name,
                "amount": str(c.amount),
                "next_date": dstr,
                "wallet": wname,
            }
        )

    keyboard = get_my_charges_keyboard(charge_data)
    await callback.message.edit_text(Texts.my_charges_title, reply_markup=keyboard)  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("charge_item_"))
async def show_charge_card(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Show details card for a charge with action buttons."""
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]

    charge_repo = ChargeRepository(session)
    charge = await charge_repo.get(callback.from_user.id, charge_id)

    if not charge:
        await callback.answer(Texts.error_not_found)
        return

    # Реальные имена + форматы через общий форматтер (TASK-0039)
    card_text = await build_charge_card_text(session, callback.from_user.id, charge)

    keyboard = get_charge_card_actions_keyboard(charge_id)
    await callback.message.edit_text(card_text, reply_markup=keyboard)  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("charge_paid_"))
async def mark_charge_paid(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Mark charge as paid using the repository logic."""
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]

    charge_repo = ChargeRepository(session)
    updated = await charge_repo.mark_paid(callback.from_user.id, charge_id)

    if not updated:
        await callback.answer(Texts.error_not_found)
        return

    if updated.status == "done":
        msg = Texts.charge_paid_once
    else:
        msg = Texts.charge_paid_periodic.format(next_date=format_date_ru(updated.next_date))

    await callback.message.edit_text(msg, reply_markup=get_main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()

    # Optionally refresh list
    # await list_charges(callback, state, session)  # but since edited, simple message ok


# Basic delete support (similar to M2 pattern)
@router.callback_query(F.data.startswith("charge_delete_"))
async def charge_delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    await state.update_data(charge_id_to_delete=charge_id)
    # For simplicity, direct delete or use confirm state
    # Here direct for demo; in full would use ConfirmDeleteStates and handler
    keyboard = get_confirm_delete_keyboard("charge", charge_id)
    await callback.message.edit_text(  # type: ignore[union-attr]
        "⚠️ Удалить это списание?",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("charge_confirm_"))
async def charge_delete(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    charge_repo = ChargeRepository(session)
    deleted = await charge_repo.delete(callback.from_user.id, charge_id)

    if deleted:
        await callback.message.edit_text(  # type: ignore[union-attr]
            Texts.charge_deleted, reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(  # type: ignore[union-attr]
            Texts.error_not_found, reply_markup=get_main_menu_keyboard()
        )
    await state.clear()
    await callback.answer()


# Note: full edit is handled in charges_create.py via charge_edit_ callbacks (reuses FSM)
# Delete uses confirm pattern (extended from M2).
# For production, move confirm logic to shared or here.

# Router test note: specific filters like F.data.startswith("charge_item_"), "charge_paid_" etc.
# Tested via dispatch in test file (see tests).
