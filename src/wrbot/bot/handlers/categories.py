"""Categories handlers — CRUD operations."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from wrbot.bot.keyboards import (
    get_cancel_keyboard,
    get_categories_keyboard,
    get_category_actions_keyboard,
    get_confirm_delete_keyboard,
)
from wrbot.bot.states import CategoryStates
from wrbot.bot.texts import Texts
from wrbot.repositories.categories import CategoryRepository
from wrbot.services.reference import DuplicateName, InvalidName, LimitExceeded, ReferenceError

logger = logging.getLogger(__name__)

router = Router(name="categories")


@router.callback_query(F.data.startswith("category_"))
async def category_details(callback: CallbackQuery) -> None:
    """Показать детали категории с действиями."""
    category_id = int(callback.data.split("_")[1])
    keyboard = get_category_actions_keyboard(category_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "category_add")
async def category_add_start(callback: CallbackQuery, state: FSMContext, **data: dict) -> None:
    """Начать добавление категории."""
    session = data["session"]
    await state.update_data(session=session, category_id=None)
    await state.set_state(CategoryStates.name)
    await callback.message.edit_text(Texts.category_enter_name, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("category_rename_"))
async def category_rename_start(
    callback: CallbackQuery, state: FSMContext, **handler_data: dict
) -> None:
    """Начать переименование категории."""
    category_id = int(callback.data.split("_")[2])
    session = handler_data["session"]
    await state.update_data(session=session, category_id=category_id)

    await state.set_state(CategoryStates.name)

    # Получаем текущее название
    repo = CategoryRepository(session)
    category = await repo.get(callback.from_user.id, category_id)
    category_name = category.name if category else "?"

    await callback.message.edit_text(
        Texts.category_enter_new_name.format(name=category_name), reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_delete_"))
async def category_delete_confirm(
    callback: CallbackQuery, state: FSMContext, **handler_data: dict
) -> None:
    """Показать подтверждение удаления категории."""
    category_id = int(callback.data.split("_")[2])
    session = handler_data["session"]

    repo = CategoryRepository(session)
    category = await repo.get(callback.from_user.id, category_id)

    if category:
        await state.update_data(category_id=category_id)
        keyboard = get_confirm_delete_keyboard("category", category_id)
        await callback.message.edit_text(
            Texts.category_confirm_delete.format(name=category.name), reply_markup=keyboard
        )

    await callback.answer()


@router.callback_query(F.data.startswith("category_confirm_"))
async def category_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """Удалить категорию."""
    state_data = await state.get_data()
    category_id = state_data.get("category_id")
    session = state_data.get("session")

    if not category_id or not session:
        await callback.answer(Texts.error_generic, show_alert=True)
        return

    repo = CategoryRepository(session)
    tg_id = callback.from_user.id

    deleted = await repo.delete(tg_id, category_id)

    if deleted:
        await callback.message.edit_text(Texts.category_deleted.format(name="?"))

        # Показать обновлённый список
        categories = await repo.list_by_user(tg_id)
        category_data = [{"id": c.id, "name": c.name} for c in categories]
        keyboard = get_categories_keyboard(category_data)

        lines = [Texts.category_list_item.format(name=c["name"]) for c in category_data]
        text = "🏷️ *Категории*\n\n" + "\n".join(lines)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.answer(Texts.error_not_found, show_alert=True)

    await state.clear()


@router.message(CategoryStates.name)
async def category_name_handler(message: Message, state: FSMContext) -> None:
    """Обработать ввод названия категории (добавление или переименование)."""
    state_data = await state.get_data()
    session = state_data.get("session")
    category_id = state_data.get("category_id")

    if not session:
        await message.answer(Texts.error_generic)
        await state.clear()
        return

    category_repo = CategoryRepository(session)
    tg_id = message.from_user.id

    try:
        if category_id is None:
            # Добавление новой категории
            category = await category_repo.create(tg_id, message.text or "")
            await message.answer(Texts.category_added.format(name=category.name))
        else:
            # Переименование существующей
            category = await category_repo.rename(tg_id, category_id, message.text or "")
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
