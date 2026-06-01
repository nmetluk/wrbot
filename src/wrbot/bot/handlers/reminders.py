"""
Handlers for reminder notifications (M4, TASK-0015).

Handles callbacks from push reminders: paid, snooze (tomorrow), edit (reuses NewChargeStates).

Specific callback prefixes (remind_*) per routing safety (TASK-0008).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from aiogram import F, Router

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery
    from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.bot.states import NewChargeStates
from wrbot.bot.texts import Texts
from wrbot.repositories.charges import ChargeRepository

logger = logging.getLogger(__name__)

router = Router(name="reminders")


@router.callback_query(F.data.startswith("remind_paid_"))  # type: ignore[untyped-decorator]
async def remind_mark_paid(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Mark charge as paid directly from the reminder notification."""
    charge_id = int(callback.data.split("_")[2])

    charge_repo = ChargeRepository(session)
    updated = await charge_repo.mark_paid(callback.from_user.id, charge_id)

    if not updated:
        await callback.answer(Texts.error_not_found)
        return

    if updated.status == "done":
        msg = Texts.reminder_paid_once
    else:
        msg = Texts.reminder_paid_periodic.format(next_date=updated.next_date)

    await callback.message.edit_text(msg, reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("remind_snooze_"))  # type: ignore[untyped-decorator]
async def remind_snooze(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Snooze this charge's reminders until tomorrow (next_date is NOT changed, per ADR-0005)."""
    charge_id = int(callback.data.split("_")[2])

    tomorrow = date.today() + timedelta(days=1)
    charge_repo = ChargeRepository(session)
    updated = await charge_repo.snooze(callback.from_user.id, charge_id, tomorrow)

    if not updated:
        await callback.answer(Texts.error_not_found)
        return

    await callback.message.edit_text(Texts.reminder_snoozed, reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("remind_edit_"))  # type: ignore[untyped-decorator]
async def remind_edit_charge(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Enter edit flow from reminder notification (reuses NewChargeStates from TASK-0012)."""
    charge_id = int(callback.data.split("_")[2])

    charge_repo = ChargeRepository(session)
    charge = await charge_repo.get(callback.from_user.id, charge_id)
    if not charge:
        await callback.answer(Texts.error_not_found)
        return

    await state.update_data(
        editing_charge_id=charge_id,
        user_id=callback.from_user.id,
        name=charge.name,
        amount=str(charge.amount),
        wallet_id=charge.wallet_id,
        category_id=charge.category_id,
        next_date=charge.next_date.isoformat() if charge.next_date else None,
        period=charge.period,
    )
    await state.set_state(NewChargeStates.name)
    await callback.message.edit_text(
        Texts.reminder_edit_started + "\n\n" + Texts.new_charge_enter_name,
        reply_markup=None,
    )
    await callback.answer()
