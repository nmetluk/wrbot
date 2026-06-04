"""Settings menu handler."""

from __future__ import annotations

import json
import logging
from datetime import time
from typing import TYPE_CHECKING, Any, cast

from aiogram import F, Router
from aiogram.filters import Command

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, Message
    from sqlalchemy.ext.asyncio import AsyncSession

from zoneinfo import ZoneInfo

from wrbot.bot.keyboards import (
    get_cancel_keyboard,
    get_categories_keyboard,
    get_global_days_edit_keyboard,
    get_global_notify_keyboard,
    get_main_menu_keyboard,
    get_settings_menu_keyboard,
    get_tz_keyboard,
    get_wallets_keyboard,
)
from wrbot.bot.states import SettingsStates
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
async def global_notify_menu(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Показать текущие глобальные настройки уведомлений (время + дни) и кнопки редактирования."""
    await state.clear()
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    tg_id = callback.from_user.id
    await user_repo.get_or_create(tg_id)

    user = await user_repo.get(tg_id)
    nt: time = user.notify_time if user else time(10, 0)
    gd_str: str = user.global_days if user else "[5,3,1]"
    try:
        gd: list[int] = json.loads(gd_str) if gd_str else []
        if not isinstance(gd, list):
            gd = [5, 3, 1]
        gd = sorted({int(x) for x in gd if isinstance(x, (int, str))})
    except Exception:
        gd = [5, 3, 1]

    time_str = f"{nt.hour:02d}:{nt.minute:02d}"
    days_str = ", ".join(str(d) for d in gd) if gd else "выключено"
    text = Texts.global_notify_current.format(time=time_str, days=days_str)
    keyboard = get_global_notify_keyboard(time_str, gd)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()


# --- Глобальные уведомления: изменение времени (TASK-0026) ---


@router.callback_query(F.data == "gnotify_time")
async def gnotify_time_start(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Начать ввод нового времени уведомлений."""
    # session текущего апдейта не сохраняем в FSM (исправление TASK-0027)
    await state.update_data()
    await state.set_state(SettingsStates.notify_time)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.global_notify_enter_time, reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(SettingsStates.notify_time)
async def process_notify_time_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Обработать ввод времени ЧЧ:ММ, валидация, сохранение, возврат к экрану глобальных."""
    text = (message.text or "").strip()
    try:
        if ":" in text:
            hh_str, mm_str = text.split(":", 1)
            hh, mm = int(hh_str), int(mm_str)
        else:
            # поддержка 0930 или 930
            clean = text.replace(" ", "")
            if len(clean) == 4:
                hh, mm = int(clean[:2]), int(clean[2:])
            elif len(clean) == 3:
                hh, mm = int(clean[:1]), int(clean[1:])
            else:
                raise ValueError
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError
        nt = time(hh, mm)
    except Exception:
        await message.answer(Texts.global_notify_invalid_time)
        return

    # session — от middleware ЭТОГО message-апдейта (не из FSM state_data!)
    if not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    user_repo = UserRepository(session)
    tg_id = message.from_user.id  # type: ignore[union-attr]
    await user_repo.set_notify_time(tg_id, nt)

    await state.clear()

    # Показать обновлённый экран глобальных уведомлений (как после input в charges/wallets)
    user = await user_repo.get(tg_id)
    nt2: time = user.notify_time if user else nt
    gd_str: str = user.global_days if user else "[5,3,1]"
    try:
        gd: list[int] = json.loads(gd_str) if gd_str else []
        gd = sorted({int(x) for x in gd if isinstance(x, (int, str))})
    except Exception:
        gd = [5, 3, 1]

    time_str = f"{nt2.hour:02d}:{nt2.minute:02d}"
    days_str = ", ".join(str(d) for d in gd) if gd else "выключено"
    view_text = Texts.global_notify_current.format(time=time_str, days=days_str)
    keyboard = get_global_notify_keyboard(time_str, gd)

    await message.answer(Texts.global_notify_time_saved.format(time=time_str))
    await message.answer(view_text, reply_markup=keyboard)


# --- Глобальные уведомления: изменение дней (TASK-0026) ---


@router.callback_query(F.data == "gnotify_days")
async def gnotify_days_start(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Открыть экран выбора/переключения дней с toggle-кнопками."""
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    tg_id = callback.from_user.id
    await user_repo.get_or_create(tg_id)
    user = await user_repo.get(tg_id)

    gd_str: str = user.global_days if user else "[5,3,1]"
    try:
        selected: list[int] = json.loads(gd_str) if gd_str else []
        selected = sorted({int(x) for x in selected if isinstance(x, (int, str))})
    except Exception:
        selected = [5, 3, 1]

    # Храним в state ТОЛЬКО selected_days (не session!)
    await state.update_data(selected_days=selected)
    await state.set_state(SettingsStates.global_days)

    days_str = ", ".join(str(d) for d in selected) if selected else "выключено"
    text = Texts.global_days_edit_title.format(current=days_str)
    keyboard = get_global_days_edit_keyboard(selected)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gday_toggle_"), SettingsStates.global_days)
async def process_gday_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Переключить день в наборе (toggle). Обновить клавиатуру на месте."""
    data = await state.get_data()
    selected: list[int] = list(data.get("selected_days", []))
    try:
        n = int((callback.data or "").rsplit("_", 1)[-1])
    except Exception:
        await callback.answer()
        return

    if n in selected:
        selected.remove(n)
    else:
        selected.append(n)
    selected = sorted(set(selected))

    await state.update_data(selected_days=selected)

    days_str = ", ".join(str(d) for d in selected) if selected else "выключено"
    text = Texts.global_days_edit_title.format(current=days_str)
    keyboard = get_global_days_edit_keyboard(selected)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "gdays_save", SettingsStates.global_days)
async def gdays_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Сохранить выбранные дни (в т.ч. [] = выкл), вернуться к экрану глобальных."""
    data = await state.get_data()
    selected: list[int] = list(data.get("selected_days", []))
    # session — свежая от middleware текущего cb-апдейта
    if not session:
        await callback.answer(Texts.error_generic, show_alert=True)
        await state.clear()
        return

    gd_str = "[]" if not selected else json.dumps(sorted(selected))
    user_repo = UserRepository(session)
    tg_id = callback.from_user.id
    await user_repo.set_global_days(tg_id, gd_str)

    await state.clear()

    # Вернуться к виду глобальных уведомлений, отредактировав текущее сообщение
    user = await user_repo.get(tg_id)
    nt: time = user.notify_time if user else time(10, 0)
    gd2_str: str = user.global_days if user else gd_str
    try:
        gd2: list[int] = json.loads(gd2_str) if gd2_str else []
        gd2 = sorted({int(x) for x in gd2 if isinstance(x, (int, str))})
    except Exception:
        gd2 = selected

    time_str = f"{nt.hour:02d}:{nt.minute:02d}"
    days_str = ", ".join(str(d) for d in gd2) if gd2 else "выключено"
    view_text = Texts.global_notify_current.format(time=time_str, days=days_str)
    keyboard = get_global_notify_keyboard(time_str, gd2)

    await callback.message.edit_text(  # type: ignore[union-attr]
        view_text, reply_markup=keyboard
    )
    await callback.answer(Texts.global_notify_days_saved)


@router.callback_query(F.data == "gdays_input", SettingsStates.global_days)
async def gnotify_days_input_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Перейти к текстовому вводу дней (альтернатива toggle)."""
    await state.update_data(days_input=True)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.global_notify_enter_days, reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(SettingsStates.global_days)
async def process_global_days_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Обработать текстовый ввод дней (из gdays_input). Сохранить и показать глобальный экран."""
    data = await state.get_data()
    if not data.get("days_input"):
        # не в режиме ввода — игнорируем или просим кнопки
        await message.answer("Используйте кнопки на экране выбора дней.")
        return

    text = (message.text or "").strip().lower()
    # session — от middleware ЭТОГО message-апдейта
    if not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    try:
        if text in ("", "0", "выкл", "off", "нет", "[]"):
            days_list: list[int] = []
        else:
            days_list = sorted(
                {int(x.strip()) for x in (message.text or "").split(",") if x.strip()}
            )
            if not days_list or any(d < 1 for d in days_list):
                raise ValueError
    except Exception:
        await message.answer(Texts.global_notify_invalid_days)
        return

    gd_str = "[]" if not days_list else json.dumps(days_list)
    user_repo = UserRepository(session)
    tg_id = message.from_user.id  # type: ignore[union-attr]
    await user_repo.set_global_days(tg_id, gd_str)

    await state.clear()

    # Показать результат + обновлённый вид
    user = await user_repo.get(tg_id)
    nt: time = user.notify_time if user else time(10, 0)
    gd2_str: str = user.global_days if user else gd_str
    try:
        gd2: list[int] = json.loads(gd2_str) if gd2_str else []
        gd2 = sorted({int(x) for x in gd2 if isinstance(x, (int, str))})
    except Exception:
        gd2 = days_list

    time_str = f"{nt.hour:02d}:{nt.minute:02d}"
    days_str = ", ".join(str(d) for d in gd2) if gd2 else "выключено"
    view_text = Texts.global_notify_current.format(time=time_str, days=days_str)
    keyboard = get_global_notify_keyboard(time_str, gd2)

    await message.answer(Texts.global_notify_days_saved)
    await message.answer(view_text, reply_markup=keyboard)


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
    wallet_data = [{"id": w.id, "name": w.name, "icon": w.icon} for w in wallets]

    if not wallet_data:
        text = Texts.wallets_list_empty
        keyboard = get_wallets_keyboard([])
    else:
        lines = [
            Texts.wallet_list_item.format(icon=w.get("icon", "👛"), name=w["name"])
            for w in wallet_data
        ]
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
    """Отменить текущее действие (диалог). Показывает «Действие отменено» + главное меню."""
    await state.clear()
    await callback.message.edit_text(Texts.action_cancelled, reply_markup=get_main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    """Отменить текущее действие (команда). Показывает «Действие отменено» + главное меню."""
    await state.clear()
    await message.answer(Texts.action_cancelled, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "settings_tz")
async def tz_menu(callback: CallbackQuery, **data: Any) -> None:
    """Показать текущий часовой пояс и меню выбора."""
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    tg_id = callback.from_user.id
    await user_repo.get_or_create(tg_id)

    user = await user_repo.get(tg_id)
    current_tz = user.tz if user else "Europe/Moscow"

    text = Texts.settings_tz_current.format(tz=current_tz)
    keyboard = get_tz_keyboard(current_tz)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text, reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tz_set_"))
async def process_tz_choice(callback: CallbackQuery, **data: Any) -> None:
    """Обработать выбор TZ из списка. Валидация + сохранение."""
    session: AsyncSession = cast("AsyncSession", data["session"])
    user_repo = UserRepository(session)
    tg_id = callback.from_user.id

    # Parse IANA from callback (tz_set_Europe_Moscow -> Europe/Moscow)
    tz_raw = (callback.data or "").replace("tz_set_", "").replace("_", "/")

    # Валидация через ZoneInfo (некорректное — отклонить)
    try:
        ZoneInfo(tz_raw)
    except Exception:
        await callback.answer(Texts.invalid_tz, show_alert=True)
        return

    await user_repo.set_tz(tg_id, tz_raw)

    # Возврат в меню настроек с подтверждением
    text = Texts.tz_changed.format(tz=tz_raw)
    from wrbot.bot.keyboards import get_settings_menu_keyboard

    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.settings_menu, reply_markup=get_settings_menu_keyboard()
    )
    await callback.answer(text)
