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
    get_cancel_keyboard,
    get_charge_categories_keyboard,
    get_charge_confirm_keyboard,
    get_charge_currency_keyboard,
    get_charge_currency_list_keyboard,
    get_charge_currency_search_results_keyboard,
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
from wrbot.services import currencies
from wrbot.services.charges import validate_charge_amount
from wrbot.services.dates import get_period_upper_bound, validate_next_date
from wrbot.services.formatters import (
    build_edit_live_card,
    build_new_charge_summary,
    format_date_ru,
    format_period_ru,
)
from wrbot.services.reference import InvalidAmount, LimitExceeded

logger = logging.getLogger(__name__)

router = Router(name="charges_create")


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    """No-op для информационных кнопок (номер страницы и т.п.)."""
    await callback.answer()


def _parse_date_ddmmyyyy(text: str) -> date | None:
    """Парсит ДД.ММ.ГГГГ, возвращает date или None."""
    try:
        d, m, y = map(int, text.strip().split("."))
        return date(y, m, d)
    except Exception:
        return None


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
        Texts.new_charge_enter_name, reply_markup=get_cancel_keyboard()
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
    await message.answer(Texts.new_charge_enter_amount, reply_markup=get_cancel_keyboard())


# 2. Сумма
@router.message(NewChargeStates.amount)
async def process_amount(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = validate_charge_amount(message.text or "")
    except InvalidAmount as e:
        await message.answer(str(e) or Texts.new_charge_invalid_amount)
        return

    await state.update_data(amount=str(amount))

    # TASK-0050: после суммы — шаг валюты (пресеты с преселектом last_currency)
    data: dict[str, Any] = await state.get_data()
    user_id: int = data.get("user_id") or message.from_user.id if message.from_user else 0
    user_repo = UserRepository(session)
    user = await user_repo.get(user_id)
    last_cur = getattr(user, "last_currency", None) or currencies.get_default()
    await state.update_data(currency=last_cur)
    await state.set_state(NewChargeStates.currency)

    if data.get("editing_charge_id"):
        # live card update on amount change (TASK-0045 e2e key) — теперь на currency step
        mid = data.get("edit_card_msg_id")
        bot = getattr(message, "bot", None)
        if mid and bot:
            try:
                card = await build_edit_live_card(
                    session, data.get("user_id", 0), await state.get_data(), "currency"
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=mid,
                    text=card,
                    reply_markup=get_cancel_keyboard(),
                )
                return
            except Exception:
                pass

    # normal: показать клавиатуру валют
    keyboard = get_charge_currency_keyboard(current=last_cur)
    await message.answer(Texts.new_charge_select_currency, reply_markup=keyboard)


# TASK-0050: 3. Валюта — пресеты
@router.callback_query(F.data.startswith("charge_currency_preset_"), NewChargeStates.currency)
async def process_currency_preset(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    code = callback.data.split("_", 3)[3]  # type: ignore[union-attr]
    if not currencies.is_valid_code(code):
        await callback.answer("Неверный код валюты")
        return
    await state.update_data(currency=code)
    await _go_to_wallet_step(callback, state, session)
    await callback.answer()


@router.callback_query(F.data == "charge_currency_other", NewChargeStates.currency)
async def process_currency_other(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Открыть постраничный список + возможность поиска."""
    items, total_pages = currencies.get_page(0, per_page=8)
    keyboard = get_charge_currency_list_keyboard(items, 0, total_pages)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_currency_list_header.format(page=1, total_pages=total_pages),
        reply_markup=keyboard,
    )
    await state.set_state(NewChargeStates.currency)  # остаёмся в currency для пагинации/выбора
    await callback.answer()


@router.callback_query(F.data.startswith("charge_currency_page_"), NewChargeStates.currency)
async def process_currency_page(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        page = int(callback.data.split("_", 3)[3])  # type: ignore[union-attr]
    except Exception:
        page = 0
    items, total_pages = currencies.get_page(page, per_page=8)
    keyboard = get_charge_currency_list_keyboard(items, page, total_pages)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_currency_list_header.format(page=page + 1, total_pages=total_pages),
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "charge_currency_back", NewChargeStates.currency)
async def process_currency_back_to_presets(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    current = data.get("currency") or currencies.get_default()
    keyboard = get_charge_currency_keyboard(current=current)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_select_currency, reply_markup=keyboard
    )
    await state.set_state(NewChargeStates.currency)
    await callback.answer()


@router.callback_query(F.data.startswith("charge_currency_choose_"), NewChargeStates.currency)
async def process_currency_choose(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    code = callback.data.split("_", 3)[3]  # type: ignore[union-attr]
    if not currencies.is_valid_code(code):
        await callback.answer("Неверная валюта")
        return
    info = currencies.get(code) or {"code": code, "name": code}
    await state.update_data(currency=code)
    await callback.answer(f"✅ {code} — {info.get('name', code)}")
    await _go_to_wallet_step(callback, state, session)


# Поиск по тексту на шаге валюты (когда показан список "Другой" или в search state)
@router.message(NewChargeStates.currency)
async def process_currency_text_as_search(message: Message, state: FSMContext) -> None:
    """Если на шаге списка валют ввели текст — трактуем как поиск."""
    query = (message.text or "").strip()
    if not query:
        return
    results = currencies.search(query)
    if not results:
        await message.answer(
            Texts.new_charge_currency_search_no_results.format(query=query),
            reply_markup=get_cancel_keyboard(),
        )
        return
    keyboard = get_charge_currency_search_results_keyboard(results)
    await message.answer(
        Texts.new_charge_currency_search_results.format(query=query), reply_markup=keyboard
    )
    await state.set_state(NewChargeStates.currency_search)


# Поиск валюты (отдельное состояние)
@router.message(NewChargeStates.currency_search)
async def process_currency_search(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    results = currencies.search(query)
    if not results:
        await message.answer(
            Texts.new_charge_currency_search_no_results.format(query=query),
            reply_markup=get_cancel_keyboard(),
        )
        return
    keyboard = get_charge_currency_search_results_keyboard(results)
    await message.answer(
        Texts.new_charge_currency_search_results.format(query=query), reply_markup=keyboard
    )


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
    await _go_to_period_step(callback, state)


@router.callback_query(F.data == "charge_skip_category", NewChargeStates.category)
async def process_skip_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(category_id=None)
    await _go_to_period_step(callback, state)


async def _go_to_period_step(callback: CallbackQuery, state: FSMContext) -> None:
    """Переход к выбору периода (TASK-0040: период перед датой)."""
    await state.set_state(NewChargeStates.period)
    keyboard = get_charge_period_keyboard()
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_select_period, reply_markup=keyboard
    )
    await callback.answer()


async def _go_to_date_step(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NewChargeStates.next_date)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_enter_date, reply_markup=None
    )
    await callback.answer()


async def _go_to_wallet_step(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Переход к кошельку после валюты (TASK-0050). Показ kb + live update при edit."""
    await state.set_state(NewChargeStates.wallet)
    data: dict[str, Any] = await state.get_data()
    if data.get("editing_charge_id"):
        mid = data.get("edit_card_msg_id")
        bot = getattr(callback, "bot", None) or getattr(callback.message, "bot", None)
        if mid and bot:
            try:
                card = await build_edit_live_card(session, data.get("user_id", 0), data, "wallet")
                chat = getattr(callback.message, "chat", None)
                chat_id = getattr(chat, "id", None) if chat else None
                if chat_id:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=mid,
                        text=card,
                        reply_markup=get_cancel_keyboard(),
                    )
                return
            except Exception:
                pass

    # обычный показ клавиатуры кошельков
    user_id: int = data.get("user_id") or callback.from_user.id
    wallet_repo = WalletRepository(session)
    wallets = await wallet_repo.list_by_user(user_id)
    if not wallets:
        await callback.message.edit_text(  # type: ignore[union-attr]
            Texts.new_charge_no_wallets, reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        return
    keyboard = get_charge_wallets_keyboard(
        [{"id": w.id, "name": w.name, "icon": w.icon} for w in wallets]
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_select_wallet, reply_markup=keyboard
    )
    await callback.answer()
    data = await state.get_data()
    # обновить live card если edit
    if data.get("editing_charge_id"):
        mid = data.get("edit_card_msg_id")
        bot = getattr(callback, "bot", None) or getattr(callback.message, "bot", None)
        if mid and bot:
            try:
                card = await build_edit_live_card(session, data.get("user_id", 0), data, "wallet")
                chat = getattr(callback.message, "chat", None)
                chat_id = getattr(chat, "id", None) if chat else None
                if chat_id:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=mid,
                        text=card,
                        reply_markup=get_cancel_keyboard(),
                    )
                return
            except Exception:
                pass

    # (wallet kb shown in _go_to_wallet_step caller path)


# 5. Дата (TASK-0040: после периода; валидация окна периода)
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

    data = await state.get_data()
    period = data.get("period")
    if not period:
        # Не должно случаться, но defensive
        period = "once"

    try:
        validate_next_date(period, d, today)  # type: ignore[arg-type]
    except ValueError:
        if period == "once":
            await message.answer(Texts.new_charge_invalid_date)
        else:
            upper = get_period_upper_bound(today, period)  # type: ignore[arg-type]
            upper_str = format_date_ru(upper)
            p_str = format_period_ru(period)
            err = Texts.new_charge_invalid_date_window.format(period=p_str, max_date=upper_str)
            await message.answer(err)
        return

    await state.update_data(next_date=d.isoformat())
    await state.set_state(NewChargeStates.notify)

    keyboard = get_charge_notify_keyboard()
    await message.answer(Texts.new_charge_select_notify, reply_markup=keyboard)


# 6. Период (TASK-0040: теперь перед датой)
@router.callback_query(F.data.startswith("charge_period_"), NewChargeStates.period)
async def process_period(callback: CallbackQuery, state: FSMContext) -> None:
    period = callback.data.split("_", 2)[2]  # type: ignore[union-attr]
    await state.update_data(period=period)
    await _go_to_date_step(callback, state)


# 7. Уведомления
@router.callback_query(F.data == "charge_notify_global")
async def process_notify_global(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(notify={"type": "global"})
    await _show_summary_and_confirm(callback, state, session)


@router.callback_query(F.data == "charge_notify_disable")
async def process_notify_disable(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(notify={"type": "disabled"})
    await _show_summary_and_confirm(callback, state, session)


@router.callback_query(F.data == "charge_notify_custom", NewChargeStates.notify)
async def process_notify_custom_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(notify={"type": "custom_pending"})
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.new_charge_enter_notify_days, reply_markup=None
    )
    await callback.answer()


@router.message(NewChargeStates.notify)
async def process_notify_days(message: Message, state: FSMContext, session: AsyncSession) -> None:
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
    await _show_summary_message(message, state, session)


async def _show_summary_and_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    user_id = data.get("user_id") or callback.from_user.id
    summary = await build_new_charge_summary(session, user_id, data)
    keyboard = get_charge_confirm_keyboard()
    await callback.message.edit_text(  # type: ignore[union-attr]
        summary, reply_markup=keyboard
    )
    await callback.answer()


async def _show_summary_message(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user_id = data.get("user_id") or message.from_user.id if message.from_user else 0
    summary = await build_new_charge_summary(session, user_id, data)
    keyboard = get_charge_confirm_keyboard()
    await message.answer(summary, reply_markup=keyboard)


# _build_summary_text удалён: теперь через build_new_charge_summary в formatters (TASK-0039)


@router.callback_query(F.data == "charge_confirm_create")
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
                currency=data.get("currency") or "RUB",
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
                currency=data.get("currency") or "RUB",
            )
            await callback.message.edit_text(  # type: ignore[union-attr]
                Texts.new_charge_created.format(
                    name=charge.name, next_date=format_date_ru(charge.next_date)
                ),
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
    """Start editing: load + live updating card (TASK-0045, no orphan drafts)."""
    charge_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    charge_repo = ChargeRepository(session)
    tg_id = callback.from_user.id
    charge = await charge_repo.get(tg_id, charge_id)
    if not charge:
        await callback.answer(Texts.error_not_found)
        return

    msg = callback.message
    msg_id = getattr(msg, "message_id", None)
    chat_id = getattr(getattr(msg, "chat", None), "id", None)

    # load + notify default if needed (для live card)
    notify_data = (
        {"type": "global"} if not charge.individual_days else {"type": "custom", "days": []}
    )
    await state.update_data(
        editing_charge_id=charge_id,
        user_id=tg_id,
        name=charge.name,
        amount=str(charge.amount),
        currency=getattr(charge, "currency", "RUB"),
        wallet_id=charge.wallet_id,
        category_id=charge.category_id,
        next_date=charge.next_date.isoformat() if charge.next_date else None,
        period=charge.period,
        notify=notify_data,
        edit_card_msg_id=msg_id,
        edit_chat_id=chat_id,
    )
    await state.set_state(NewChargeStates.name)

    # live card via formatter (TASK-0039) + prompt
    card = await build_edit_live_card(session, tg_id, await state.get_data(), "name")
    await callback.message.edit_text(  # type: ignore[union-attr]
        card, reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


# Поддержка отмены в любом состоянии charge flow (создание/редактирование)
@router.callback_query(F.data == "cancel", NewChargeStates)
async def cancel_charge_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена диалога (создание/редакт): «Действие отменено» + меню (TASK-0037)."""
    await state.clear()
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.action_cancelled, reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
