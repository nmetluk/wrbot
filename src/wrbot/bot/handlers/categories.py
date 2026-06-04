"""Categories handlers — CRUD operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aiogram import F, Router

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import CallbackQuery, Message
    from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import IntegrityError

from wrbot.bot.keyboards import (
    get_cancel_keyboard,
    get_categories_keyboard,
    get_category_actions_keyboard,
    get_category_notify_keyboard,
    get_confirm_delete_keyboard,
)
from wrbot.bot.states import CategoryStates
from wrbot.bot.texts import Texts
from wrbot.bot.validators import parse_chat_id
from wrbot.repositories.categories import CategoryRepository
from wrbot.services.reference import DuplicateName, InvalidName, LimitExceeded, ReferenceError

logger = logging.getLogger(__name__)

router = Router(name="categories")


@router.callback_query(F.data.startswith("category_item_"))
async def category_details(callback: CallbackQuery) -> None:
    """Показать детали категории с действиями."""
    category_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    keyboard = get_category_actions_keyboard(category_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "category_add")
async def category_add_start(callback: CallbackQuery, state: FSMContext, **data: Any) -> None:
    """Начать добавление категории."""
    # session из middleware текущего апдейта (НЕ храним в FSM)
    await state.update_data(category_id=None)
    await state.set_state(CategoryStates.name)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.category_enter_name, reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_rename_"))
async def category_rename_start(
    callback: CallbackQuery, state: FSMContext, **handler_data: Any
) -> None:
    """Начать переименование категории."""
    category_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    session: AsyncSession = cast("AsyncSession", handler_data["session"])
    # НЕ храним session в FSM, только category_id
    await state.update_data(category_id=category_id)

    await state.set_state(CategoryStates.name)

    # Получаем текущее название
    repo = CategoryRepository(session)
    tg_id = callback.from_user.id
    category = await repo.get(tg_id, category_id)
    category_name = category.name if category else "?"

    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.category_enter_new_name.format(name=category_name), reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_delete_"))
async def category_delete_confirm(
    callback: CallbackQuery, state: FSMContext, **handler_data: Any
) -> None:
    """Показать подтверждение удаления категории."""
    category_id = int(callback.data.split("_")[2])  # type: ignore[union-attr]
    session: AsyncSession = cast("AsyncSession", handler_data["session"])

    repo = CategoryRepository(session)
    tg_id = callback.from_user.id
    category = await repo.get(tg_id, category_id)

    if category:
        await state.update_data(category_id=category_id)
        keyboard = get_confirm_delete_keyboard("category", category_id)
        await callback.message.edit_text(  # type: ignore[union-attr]
            Texts.category_confirm_delete.format(name=category.name), reply_markup=keyboard
        )

    await callback.answer()


@router.callback_query(F.data.startswith("category_confirm_"))
async def category_delete(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Удалить категорию."""
    # session из middleware текущего апдейта
    state_data = await state.get_data()
    category_id = state_data.get("category_id")

    if not category_id or not session:
        await callback.answer(Texts.error_generic, show_alert=True)
        return

    repo = CategoryRepository(session)
    tg_id = callback.from_user.id

    try:
        deleted = await repo.delete(tg_id, category_id)
    except IntegrityError:
        # На случай будущих ограничений (SET NULL обычно не падает)
        logger.info("Integrity error on category delete (unexpected): category_id=%s", category_id)
        await callback.answer(Texts.error_generic, show_alert=True)
        await state.clear()
        return

    if deleted:
        await callback.message.edit_text(Texts.category_deleted.format(name="?"))  # type: ignore[union-attr]

        # Показать обновлённый список
        categories = await repo.list_by_user(tg_id)
        category_data = [{"id": c.id, "name": c.name} for c in categories]
        keyboard = get_categories_keyboard(category_data)

        lines = [Texts.category_list_item.format(name=c["name"]) for c in category_data]
        text = "🏷️ *Категории*\n\n" + "\n".join(lines)
        await callback.message.edit_text(text, reply_markup=keyboard)  # type: ignore[union-attr]
    else:
        await callback.answer(Texts.error_not_found, show_alert=True)

    await state.clear()


@router.message(CategoryStates.name)
async def category_name_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Обработать ввод названия категории (добавление или переименование)."""
    # session — свежая от middleware текущего message-апдейта
    state_data = await state.get_data()
    category_id = state_data.get("category_id")

    if not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    category_repo = CategoryRepository(session)
    tg_id = message.from_user.id  # type: ignore[union-attr]

    try:
        if category_id is None:
            # Добавление новой категории
            category = await category_repo.create(tg_id, message.text or "")
            await message.answer(Texts.category_added.format(name=category.name))
        else:
            # Переименование существующей
            category = await category_repo.rename(tg_id, category_id, message.text or "")  # type: ignore[assignment]
            if category:
                await message.answer(Texts.category_renamed.format(name=category.name))
            else:
                await message.answer(Texts.error_not_found)
                await state.clear()
                return

        # Показать обновлённый список
        categories = await category_repo.list_by_user(tg_id)
        category_data = [{"id": c.id, "name": c.name} for c in categories]
        keyboard = get_categories_keyboard(category_data)

        lines = [Texts.category_list_item.format(name=c["name"]) for c in category_data]
        text = "🏷️ *Категории*\n\n" + "\n".join(lines)
        await message.answer(text, reply_markup=keyboard)

    except InvalidName as e:
        if "пуст" in str(e):
            await message.answer(Texts.error_empty_name)
        else:
            settings = __import__("wrbot.config").config.get_settings()
            await message.answer(Texts.error_name_too_long.format(max=100))
    except LimitExceeded:
        settings = __import__("wrbot.config").config.get_settings()
        await message.answer(Texts.error_limit_exceeded.format(max=settings.max_categories))
    except DuplicateName:
        await message.answer(Texts.error_duplicate_name)
    except ReferenceError as e:
        logger.error("Category error: %s", e)
        await message.answer(Texts.error_generic)

    await state.clear()


# TASK-0043: управление целями дубля напоминаний (Category.notify_chat_ids)


@router.callback_query(F.data.startswith("category_notify_"))
async def category_notify_list(
    callback: CallbackQuery, state: FSMContext, **handler_data: Any
) -> None:
    """Показать список целей (chat_id) + кнопки удаления/добавить."""
    data = callback.data or ""
    # Более специфичные remove_/add_ обрабатываются отдельными хэндлерами.
    # Гард: если это remove/add — не обрабатываем здесь.
    if any(x in data for x in ("_remove_", "_add_")):
        return
    parts = data.split("_")
    category_id = int(parts[-1]) if parts[-1].lstrip("-").isdigit() else int(parts[2])
    session: AsyncSession = cast("AsyncSession", handler_data["session"])
    tg_id = callback.from_user.id

    repo = CategoryRepository(session)
    cat = await repo.get(tg_id, category_id)
    targets = await repo.get_notify_chat_ids(tg_id, category_id) if cat else []

    name = cat.name if cat else "?"
    title = Texts.category_notify_title.format(name=name)
    if not targets:
        title += "\n\n" + Texts.category_notify_empty

    kb = get_category_notify_keyboard(category_id, targets)
    await callback.message.edit_text(title, reply_markup=kb)  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("category_notify_remove_"))
async def category_notify_remove(
    callback: CallbackQuery, state: FSMContext, **handler_data: Any
) -> None:
    """Удалить одну цель по chat_id из callback."""
    # category_notify_remove_{cat}_{chatid}
    parts = (callback.data or "").split("_")
    # parts: ['category','notify','remove', cat, chat... ] chat may have -
    category_id = int(parts[3])
    chat_str = "_".join(parts[4:])  # на случай, но обычно один токен
    chat_id = int(chat_str)
    session: AsyncSession = cast("AsyncSession", handler_data["session"])
    tg_id = callback.from_user.id

    repo = CategoryRepository(session)
    await repo.remove_notify_chat_id(tg_id, category_id, chat_id)

    # refresh list
    cat = await repo.get(tg_id, category_id)
    targets = await repo.get_notify_chat_ids(tg_id, category_id) if cat else []
    name = cat.name if cat else "?"
    title = Texts.category_notify_title.format(name=name)
    if not targets:
        title += "\n\n" + Texts.category_notify_empty
    kb = get_category_notify_keyboard(category_id, targets)
    await callback.message.edit_text(title, reply_markup=kb)  # type: ignore[union-attr]
    await callback.answer(Texts.category_notify_removed.format(chat_id=chat_id))


@router.callback_query(F.data.startswith("category_notify_add_"))
async def category_notify_add_start(
    callback: CallbackQuery, state: FSMContext, **handler_data: Any
) -> None:
    """Начать ввод chat_id для добавления цели."""
    category_id = int(callback.data.split("_")[-1])  # type: ignore[union-attr]
    await state.update_data(category_id=category_id, notify_for_cat=category_id)
    await state.set_state(CategoryStates.notify_chat_id)
    await callback.message.edit_text(  # type: ignore[union-attr]
        Texts.category_notify_enter_chat_id, reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(CategoryStates.notify_chat_id)
async def category_notify_chat_id_handler(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Обработать ввод chat_id, валидация, добавить, показать обновлённый список."""
    state_data = await state.get_data()
    category_id = state_data.get("category_id") or state_data.get("notify_for_cat")
    if not category_id or not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    tg_id = message.from_user.id  # type: ignore[union-attr]
    chat_id = parse_chat_id(message.text)

    repo = CategoryRepository(session)
    cat = await repo.get(tg_id, category_id)

    if chat_id is None:
        await message.answer(Texts.category_notify_invalid_chat_id)
        # оставляем в state для повторного ввода
        return

    if not cat:
        await message.answer(Texts.error_not_found)
        await state.clear()
        return

    added = await repo.add_notify_chat_id(tg_id, category_id, chat_id)
    if added:
        await message.answer(Texts.category_notify_added.format(chat_id=chat_id, name=cat.name))
    else:
        await message.answer("ℹ️ Уже в списке.")

    # показать обновлённый экран списка целей
    targets = await repo.get_notify_chat_ids(tg_id, category_id)
    title = Texts.category_notify_title.format(name=cat.name)
    if not targets:
        title += "\n\n" + Texts.category_notify_empty
    kb = get_category_notify_keyboard(category_id, targets)
    await message.answer(title, reply_markup=kb)

    await state.clear()
