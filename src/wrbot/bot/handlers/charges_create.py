"""
FSM handlers for creating a new charge (M3, TASK-0011).

Пошаговый диалог создания списания (M3).
Сохранение через ChargeRepository.
Поддержка /cancel и кнопки Отмена.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from aiogram import F, Router

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, Message
    from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.bot.keyboards import (
    get_charge_categories_keyboard,
    get_charge_confirm_keyboard,
    get_charge_notify_keyboard,
    get_charge_period_keyboard,
    get_charge_wallets_keyboard,  # для возврата после добавления
    get_main_menu_keyboard,
)
from wrbot.bot.states import NewChargeStates, WalletStates
from wrbot.bot.texts import Texts
from wrbot.repositories.categories import CategoryRepository
from wrbot.repositories.charges import ChargeRepository
from wrbot.repositories.users import UserRepository
from wrbot.repositories.wallets import WalletRepository
from wrbot.services.charges import validate_charge_amount
from wrbot.services.reference import InvalidAmount, LimitExceeded

logger = logging.getLogger(__name__)

router = Router(name="charges_create")


def _parse_date_ddmmyyyy(text: str) -> date | None:
    """Парсит ДД.ММ.ГГГГ, возвращает date или None."""
    try:
        d, m, y = map(int, text.strip().split("."))
        return date(y, m, d)
    except Exception:
        return None


def _format_period(period: str) -> str:
    mapping = {
        "once": "одноразово",
        "monthly": "ежемесячно",
        "quarterly": "ежеквартально",
        "yearly": "ежегодно",
    }
    return mapping.get(period, period)


def _format_notify(notify_data: dict[str, Any] | None) -> str:
    if not notify_data:
        return "глобальные"
    if notify_data.get("disabled"):
        return "отключены"
    days = notify_data.get("days")
    if days:
        return f"свои: {', '.join(map(str, days))}"
    return "глобальные"


@router.callback_query(F.data == "new_charge")
async def new_charge_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Начало создания списания."""
    user_repo = UserRepository(session)
    await user_repo.get_or_create(callback.from_user.id)  # ensure user

    await state.set_state(NewChargeStates.name)
    await state.update_data(user_id=callback.from_user.id)

    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_enter_name, reply_markup=None
    )
    await callback.answer()


# 1. Название
@router.message(NewChargeStates.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer(Texts.error_empty_name)
        return
    if len(name) > 100:
        await message.answer(Texts.error_name_too_long.format(max=100))
        return

    await state.update_data(name=name)
    await state.set_state(NewChargeStates.amount)
    await message.answer(Texts.new_charge_enter_amount)


# 2. Сумма
@router.message(NewChargeStates.amount)
async def process_amount(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = validate_charge_amount(message.text or "")
    except InvalidAmount as e:
        await message.answer(str(e) or Texts.new_charge_invalid_amount)
        return

    await state.update_data(amount=str(amount))
    await state.set_state(NewChargeStates.wallet)

    # Показать выбор кошелька СРАЗУ (TASK-0035 hotfix): грузим и шлём kb в этом же сообщении,
    # без отдельного @router.message(NewChargeStates.wallet) и без ожидания доп. сообщения от юзера.
    data: dict[str, Any] = await state.get_data()
    user_id: int = data.get("user_id") or 0
    wallet_repo = WalletRepository(session)
    wallets = await wallet_repo.list_by_user(user_id)
    if not wallets:
        await message.answer(Texts.new_charge_no_wallets)
    keyboard = get_charge_wallets_keyboard([{"id": w.id, "name": w.name} for w in wallets])
    await message.answer(Texts.new_charge_select_wallet, reply_markup=keyboard)


# Обработка выбора кошелька в charge flow
@router.callback_query(F.data.startswith("charge_wallet_"), NewChargeStates.wallet)
async def process_charge_wallet_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    wallet_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]

    await state.update_data(wallet_id=wallet_id)
    await state.set_state(NewChargeStates.category)

    # Показать категории
    cat_repo = CategoryRepository(session)
    cats = await cat_repo.list_by_user(callback.from_user.id)

    keyboard = get_charge_categories_keyboard([{"id": c.id, "name": c.name} for c in cats])
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_select_category, reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "charge_add_wallet", NewChargeStates.wallet)
async def start_add_wallet_in_charge(callback: CallbackQuery, state: FSMContext) -> None:
    """Переход к созданию нового кошелька с возвратом в поток создания списания."""
    await state.update_data(return_to="charge_wallet")  # флаг для возврата
    await state.set_state(WalletStates.name)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.wallet_enter_name, reply_markup=None
    )
    await callback.answer()


# 4. Категория (или пропуск)
@router.callback_query(F.data.startswith("charge_category_"), NewChargeStates.category)
async def process_charge_category_choice(callback: CallbackQuery, state: FSMContext) -> None:
    cat_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    await state.update_data(category_id=cat_id)
    await _go_to_date_step(callback, state)


@router.callback_query(F.data == "charge_skip_category", NewChargeStates.category)
async def process_skip_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(category_id=None)
    await _go_to_date_step(callback, state)


async def _go_to_date_step(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NewChargeStates.next_date)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_enter_date, reply_markup=None
    )
    await callback.answer()


# 5. Дата
@router.message(NewChargeStates.next_date)
async def process_next_date(message: Message, state: FSMContext) -> None:
    d = _parse_date_ddmmyyyy(message.text or "")
    if not d:
        await message.answer(Texts.new_charge_invalid_date)
        return

    today = date.today()
    if d <= today:
        await message.answer(Texts.new_charge_invalid_date)
        return

    await state.update_data(next_date=d.isoformat())
    await state.set_state(NewChargeStates.period)

    keyboard = get_charge_period_keyboard()
    await message.answer(Texts.new_charge_select_period, reply_markup=keyboard)


# 6. Период
@router.callback_query(F.data.startswith("charge_period_"), NewChargeStates.period)
async def process_period(callback: CallbackQuery, state: FSMContext) -> None:
    period = callback.data.split("_", 2)[2]  # type: ignore[union-attr]
    await state.update_data(period=period)
    await state.set_state(NewChargeStates.notify)

    keyboard = get_charge_notify_keyboard()
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_select_notify, reply_markup=keyboard
    )
    await callback.answer()


# 7. Уведомления
@router.callback_query(F.data == "charge_notify_global", NewChargeStates.notify)
async def process_notify_global(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(notify={"type": "global"})
    await _show_summary_and_confirm(callback, state)


@router.callback_query(F.data == "charge_notify_disable", NewChargeStates.notify)
async def process_notify_disable(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(notify={"type": "disabled"})
    await _show_summary_and_confirm(callback, state)


@router.callback_query(F.data == "charge_notify_custom", NewChargeStates.notify)
async def process_notify_custom_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(notify={"type": "custom_pending"})
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_enter_notify_days, reply_markup=None
    )
    await callback.answer()


@router.message(NewChargeStates.notify)
async def process_notify_days(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        days = sorted({int(x.strip()) for x in text.split(",") if x.strip()})
        if not days or any(d < 1 or d > 30 for d in days):
            raise ValueError
    except Exception:
        await message.answer(Texts.new_charge_invalid_notify_days)
        return

    await state.update_data(notify={"type": "custom", "days": days})
    # Показать summary (нужен callback context, но здесь message)
    # Для простоты: сразу идем к confirm, но summary покажем в следующем сообщении
    await _show_summary_message(message, state)


async def _show_summary_and_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    summary = _build_summary_text(data)
    keyboard = get_charge_confirm_keyboard()
    await callback.message.edit_text(  # type: ignore[union-attr]
        summary, reply_markup=keyboard
    )
    await callback.answer()


async def _show_summary_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    summary = _build_summary_text(data)
    keyboard = get_charge_confirm_keyboard()
    await message.answer(summary, reply_markup=keyboard)


def _build_summary_text(data: dict[str, Any]) -> str:
    return Texts.new_charge_summary.format(
        name=data.get("name", "?"),
        amount=data.get("amount", "?"),
        wallet="выбран",
        category="выбрана" if data.get("category_id") else "пропущена",
        next_date=data.get("next_date", "?"),
        period=_format_period(data.get("period", "")),
        notify=_format_notify(data.get("notify")),
    )


@router.callback_query(F.data == "charge_confirm_create", NewChargeStates.notify)
async def confirm_create_charge(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    user_id = data["user_id"]
    editing_id = data.get("editing_charge_id")

    charge_repo = ChargeRepository(session)
    user_repo = UserRepository(session)
    await user_repo.get_or_create(user_id)

    try:
        if editing_id:
            charge = await charge_repo.update(
                user_id,
                editing_id,
                name=data["name"],
                amount=Decimal(data["amount"]),
                wallet_id=data["wallet_id"],
                category_id=data.get("category_id"),
                next_date=date.fromisoformat(data["next_date"]),
                period=data["period"],
            )
            await callback.message.edit_text(  # type: ignore[union-attr]
                Texts.charge_edit_saved,
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            charge = await charge_repo.create(
                user_id=user_id,
                name=data["name"],
                amount=Decimal(data["amount"]),
                wallet_id=data["wallet_id"],
                category_id=data.get("category_id"),
                next_date=date.fromisoformat(data["next_date"]),
                period=data["period"],
            )
            await callback.message.edit_text(  # type: ignore[union-attr]
                Texts.new_charge_created.format(name=charge.name, next_date=charge.next_date),
                reply_markup=get_main_menu_keyboard(),
            )
    except (InvalidAmount, LimitExceeded) as e:
        await callback.message.edit_text(str(e), reply_markup=get_main_menu_keyboard())  # type: ignore[union-attr]
    except Exception:
        logger.exception("Failed to save charge")
        await callback.message.edit_text(Texts.error_generic, reply_markup=get_main_menu_keyboard())  # type: ignore[union-attr]
    finally:
        await state.clear()
        await callback.answer()


@router.callback_query(F.data.startswith("charge_edit_"))
async def start_edit_charge(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Start editing a charge by loading data into NewChargeStates FSM."""
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
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
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.charge_edit_started + "\n\n" + Texts.new_charge_enter_name,
        reply_markup=None,
    )
    await callback.answer()


# Поддержка отмены в любом состоянии charge flow
@router.callback_query(F.data == "cancel", NewChargeStates)
async def cancel_charge_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_cancelled, reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
