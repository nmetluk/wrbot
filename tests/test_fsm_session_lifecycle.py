"""
Интеграционный тест жизненного цикла сессии (TASK-0027).

Проверяет, что FSM continuation-хэндлеры используют сессию *текущего* апдейта
(прокинутую DbSessionMiddleware), а не сохранённую в FSM state.update_data(session=...).

Тест:
- Использует реальную фабрику сессий + DbSessionMiddleware (две итерации апдейтов).
- Реальный FSMContext (MemoryStorage) для state.get_data / update_data / set_state.
- Реальная SQLite (через test_engine + alembic).
- Для каждого основного FSM-write сценария (wallets, categories, settings time/days):
  - "update 1": старт шага (cb) — через mw
  - "update 2": continuation (message или cb save) — через mw со СВОЕЙ сессией
  - После второго коммита проверяем, что запись реально сохранилась в БД.

Тест ПАДАЕТ на коде до фикса (потеря записи) и проходит после.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wrbot.bot.handlers import categories as categories_handler
from wrbot.bot.handlers import settings as settings_handler
from wrbot.bot.handlers import wallets as wallets_handler
from wrbot.bot.middlewares.db import DbSessionMiddleware
from wrbot.repositories.users import UserRepository
from wrbot.repositories.wallets import WalletRepository


def _make_tg_user(uid: int = 12345) -> User:
    u = MagicMock(spec=User)
    u.id = uid
    u.is_bot = False
    u.first_name = "Test"
    return u


def _make_cb(data: str, uid: int = 12345) -> CallbackQuery:
    cb = AsyncMock(spec=CallbackQuery)
    cb.data = data
    cb.message = AsyncMock()
    cb.answer = AsyncMock()
    cb.from_user = _make_tg_user(uid)
    return cb


def _make_msg(text: str, uid: int = 12345) -> Message:
    m = AsyncMock(spec=Message)
    m.text = text
    m.answer = AsyncMock()
    m.from_user = _make_tg_user(uid)
    return m


def _make_fsm(uid: int = 12345) -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(chat_id=uid, user_id=uid, bot_id=1)
    return FSMContext(storage=storage, key=key)


@pytest.mark.asyncio
async def test_fsm_lifecycle_wallet_create_persists(test_engine):
    """Кошелёк: add_start (update1) + name_handler (update2) — запись сохраняется."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    mw = DbSessionMiddleware(factory)
    state = _make_fsm(12345)

    # Предварительно создаём пользователя (FK)
    async with factory() as s0:
        await UserRepository(s0).get_or_create(12345)
        await s0.commit()

    # update 1: старт добавления
    cb = _make_cb("wallet_add")
    data: dict = {}

    async def dispatch1(event, d):
        await wallets_handler.wallet_add_start(event, state=state, **d)

    await mw(dispatch1, cb, data)

    # update 2: ввод имени (continuation)
    msg = _make_msg("КошелёкЖизни")
    data = {}

    async def dispatch2(event, d):
        sess = d["session"]
        await wallets_handler.wallet_name_handler(event, state=state, session=sess)

    await mw(dispatch2, msg, data)

    # Проверка: запись реально в БД
    async with factory() as check:
        repo = WalletRepository(check)
        ws = await repo.list_by_user(12345)
        assert len(ws) == 1
        assert ws[0].name == "КошелёкЖизни"


@pytest.mark.asyncio
async def test_fsm_lifecycle_category_create_persists(test_engine):
    """Категория: add_start + name_handler — запись сохраняется."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    mw = DbSessionMiddleware(factory)
    state = _make_fsm(12345)

    async with factory() as s0:
        await UserRepository(s0).get_or_create(12345)
        await s0.commit()

    cb = _make_cb("category_add")
    data = {}

    async def dispatch1(event, d):
        await categories_handler.category_add_start(event, state=state, **d)

    await mw(dispatch1, cb, data)

    msg = _make_msg("Зарплата")
    data = {}

    async def dispatch2(event, d):
        sess = d["session"]
        await categories_handler.category_name_handler(event, state=state, session=sess)

    await mw(dispatch2, msg, data)

    async with factory() as check:
        from wrbot.repositories.categories import CategoryRepository

        repo = CategoryRepository(check)
        cats = await repo.list_by_user(12345)
        assert len(cats) == 1
        assert cats[0].name == "Зарплата"


@pytest.mark.asyncio
async def test_fsm_lifecycle_settings_notify_time_persists(test_engine):
    """Глобальное время: gnotify_time_start + process_notify_time_input — сохраняется."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    mw = DbSessionMiddleware(factory)
    state = _make_fsm(12345)

    # Пользователь с дефолтом
    async with factory() as s0:
        await UserRepository(s0).get_or_create(12345)
        await s0.commit()

    # update 1: нажали "изменить время"
    cb = _make_cb("gnotify_time")
    data = {}

    async def dispatch1(event, d):
        await settings_handler.gnotify_time_start(event, state=state, **d)

    await mw(dispatch1, cb, data)

    # update 2: ввели новое время
    msg = _make_msg("09:30")
    data = {}

    async def dispatch2(event, d):
        sess = d["session"]
        await settings_handler.process_notify_time_input(event, state=state, session=sess)

    await mw(dispatch2, msg, data)

    # проверка
    async with factory() as check:
        u = await UserRepository(check).get(12345)
        assert u is not None
        assert f"{u.notify_time.hour:02d}:{u.notify_time.minute:02d}" == "09:30"


@pytest.mark.asyncio
async def test_fsm_lifecycle_settings_global_days_persists(test_engine):
    """Глобальные дни: gnotify_days_start + gdays_save — сохраняется (в т.ч. смена на [1,7])."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    mw = DbSessionMiddleware(factory)
    state = _make_fsm(12345)

    async with factory() as s0:
        await UserRepository(s0).get_or_create(12345)
        await s0.commit()

    # update 1: открыть дни (загружает текущие и кладёт selected_days в state)
    cb = _make_cb("gnotify_days")
    data = {}

    async def dispatch1(event, d):
        await settings_handler.gnotify_days_start(event, state=state, **d)

    await mw(dispatch1, cb, data)

    # Имитируем выбор других дней (как будто несколько toggle)
    await state.update_data(selected_days=[1, 7])

    # update 2: сохранить
    cb_save = _make_cb("gdays_save")
    data = {}

    async def dispatch_save(event, d):
        sess = d["session"]
        await settings_handler.gdays_save(event, state=state, session=sess)

    await mw(dispatch_save, cb_save, data)

    # проверка
    async with factory() as check:
        u = await UserRepository(check).get(12345)
        assert u is not None
        assert u.global_days in ("[1, 7]", "[1,7]")


@pytest.mark.asyncio
async def test_fsm_lifecycle_uses_fresh_session_per_update(test_engine):
    """
    Дополнительная проверка: continuation-хэндлер получает именно ту сессию,
    которую middleware предоставил для ЭТОГО апдейта (а не старую из state).
    """
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    mw = DbSessionMiddleware(factory)
    state = _make_fsm(12345)

    async with factory() as s0:
        await UserRepository(s0).get_or_create(12345)
        await s0.commit()

    # update1 для времени
    cb = _make_cb("gnotify_time")
    data = {}

    async def d1(e, d):
        await settings_handler.gnotify_time_start(e, state=state, **d)

    await mw(d1, cb, data)

    # update2
    msg = _make_msg("08:45")
    data = {}

    async def d2(e, d):
        sess = d["session"]
        await settings_handler.process_notify_time_input(e, state=state, session=sess)

    await mw(d2, msg, data)

    # Должно сохраниться 08:45 (а не дефолт)
    async with factory() as check:
        u = await UserRepository(check).get(12345)
        assert f"{u.notify_time.hour:02d}:{u.notify_time.minute:02d}" == "08:45"
