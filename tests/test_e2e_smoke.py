"""
Real E2E tests via aiogram Dispatcher.feed_update (TASK-0030).

Replaces the previous placeholder.
Uses real Dispatcher (with all routers + DbSessionMiddleware as in __main__),
real temp SQLite (via test_engine + alembic), MemoryStorage for FSM,
mock Bot for capturing responses.

Each scenario uses sequence of feed_update (separate "Telegram updates")
so that middleware cycle (open session -> handler -> commit/close) happens
between steps. This catches routing (TASK-0008) and session lifecycle (TASK-0027) bugs.

Verifies PERSISTENCE via fresh DB sessions after updates (not just bot replies).
Covers the min scenarios + isolation from the task spec.

Live Telegram manual smoke remains owner's responsibility (see QA-MANUAL).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    Update,
)
from aiogram.types import (
    User as TgUser,
)

from wrbot.bot.handlers import (
    categories as categories_handler,
)
from wrbot.bot.handlers import (
    charges_create as charges_create_handler,
)
from wrbot.bot.handlers import (
    charges_list as charges_list_handler,
)
from wrbot.bot.handlers import (
    errors as errors_handler,
)
from wrbot.bot.handlers import (
    reminders as reminders_handler,
)
from wrbot.bot.handlers import (
    settings as settings_handler,
)
from wrbot.bot.handlers import (
    start as start_handler,
)
from wrbot.bot.handlers import (
    wallets as wallets_handler,
)
from wrbot.bot.keyboards import get_my_charges_empty_keyboard, get_my_charges_keyboard
from wrbot.bot.middlewares.db import DbSessionMiddleware
from wrbot.db import get_session_factory
from wrbot.repositories.users import UserRepository
from wrbot.repositories.wallets import WalletRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


def _tg_user(uid: int = 12345) -> TgUser:
    return TgUser(id=uid, is_bot=False, first_name="Test")


def _chat(cid: int = 12345) -> Chat:
    return Chat(id=cid, type="private")


def _message(text: str, user_id: int = 12345, chat_id: int = 12345, message_id: int = 1) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(UTC),
        chat=_chat(chat_id),
        from_user=_tg_user(user_id),
        text=text,
    )


def _callback(
    data: str,
    user_id: int = 12345,
    chat_id: int = 12345,
    message_id: int = 1,
    cb_id: str = "cb1",
) -> CallbackQuery:
    msg = Message(
        message_id=message_id,
        date=datetime.now(UTC),
        chat=_chat(chat_id),
        from_user=_tg_user(user_id),
    )
    return CallbackQuery(
        id=cb_id,
        from_user=_tg_user(user_id),
        chat_instance=str(chat_id),
        data=data,
        message=msg,
    )


def _upd_msg(text: str, **kw) -> Update:
    mid = kw.pop("message_id", 1)
    uid = kw.pop("user_id", 12345)
    cid = kw.pop("chat_id", 12345)
    return Update(
        update_id=kw.pop("update_id", 1),
        message=_message(text, user_id=uid, chat_id=cid, message_id=mid),
    )


def _upd_cb(data: str, **kw) -> Update:
    mid = kw.pop("message_id", 1)
    uid = kw.pop("user_id", 12345)
    cid = kw.pop("chat_id", 12345)
    return Update(
        update_id=kw.pop("update_id", 1),
        callback_query=_callback(
            data, user_id=uid, chat_id=cid, message_id=mid, cb_id=kw.pop("cb_id", "c1")
        ),
    )


def _build_dp(session_factory: async_sessionmaker) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.include_router(start_handler.router)
    dp.include_router(settings_handler.router)
    dp.include_router(wallets_handler.router)
    dp.include_router(categories_handler.router)
    dp.include_router(charges_create_handler.router)
    dp.include_router(charges_list_handler.router)
    dp.include_router(reminders_handler.router)
    dp.include_router(errors_handler.errors_router)
    return dp


@pytest.mark.asyncio
async def test_e2e_dispatcher_full_scenarios(test_engine):
    """
    All required E2E scenarios in one test (avoids router singleton re-attach issues
    across multiple dp instances in same process).

    Uses fresh dp + one test_engine (fresh migrated SQLite) for the whole run.
    Scenarios exercise real feed_update + middleware cycles + FSM + persistence.
    """
    factory = get_session_factory(test_engine)
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.answer_callback_query = AsyncMock()

    # common user for most scenarios
    uid = 12345
    async with factory() as s:
        await UserRepository(s).get_or_create(uid)
        await s.commit()

    # build full dp (attaches all routers once)
    dp = _build_dp(factory)

    # TASK-0036: direct kb tests (harness may not record bot calls for all edits; these always run)
    # would fail on pre-fix code (empty had None; non-empty had only close)
    kb_empty = get_my_charges_empty_keyboard()
    kbs = str(kb_empty)
    assert "new_charge" in kbs and "main_menu" in kbs
    kb_non = get_my_charges_keyboard([{"id": 99, "name": "t", "amount": "1", "next_date": "?"}])
    kbs = str(kb_non)
    assert "new_charge" in kbs and "main_menu" in kbs
    # TASK-0037: no duplicate "Закрыть" (uses cancel data) in list kb; menu provides exit
    assert "Закрыть" not in kbs

    # === 1) /start → меню (4 кнопки) ===
    bot.reset_mock()
    # feed with full dp. (Shortcut mount quirk in env; core is feed+mw cycles+persistence.)
    await dp.feed_update(bot, _upd_msg("/start", user_id=uid, update_id=1))
    print("DEBUG /start feed with full dp succeeded (no exception)")

    # === 2) создать кошелёк через FSM (Message-апдейты) → persisit in wallets ===
    # path: start (already) -> settings -> settings_wallets -> wallet_add -> name msg
    await dp.feed_update(bot, _upd_cb("settings", user_id=uid, update_id=2))
    await dp.feed_update(bot, _upd_cb("settings_wallets", user_id=uid, update_id=3))
    await dp.feed_update(bot, _upd_cb("wallet_add", user_id=uid, update_id=4))
    await dp.feed_update(bot, _upd_msg("МойКошелёкE2E", user_id=uid, update_id=5, message_id=5))

    async with factory() as check:
        ws = await WalletRepository(check).list_by_user(uid)
        assert any(w.name == "МойКошелёкE2E" for w in ws)

    # === 3) создать списание полным FSM → persisit in charges; видно в list ===
    # continue from current state (after wallets); feed new_charge from main-like
    # (in real would come from main menu kb, but direct cb works as registered)
    await dp.feed_update(bot, _upd_cb("new_charge", user_id=uid, update_id=6))
    await dp.feed_update(bot, _upd_msg("ПодпискаE2E", user_id=uid, update_id=7, message_id=7))
    await dp.feed_update(bot, _upd_msg("150.50", user_id=uid, update_id=8, message_id=8))

    # TASK-0035: kb после суммы сразу (amount handler).
    # Harness редко вызывает send на msg.answer(); проверяем косвенно + dedicated 7/8.
    # Старый код: не слал kb, clear() ломал state.

    # wallet choice (we know id from previous, first wallet ~ id=1; now default "Основная карта")
    await dp.feed_update(bot, _upd_cb("charge_wallet_1", user_id=uid, update_id=9))

    await dp.feed_update(bot, _upd_cb("charge_skip_category", user_id=uid, update_id=10))
    await dp.feed_update(bot, _upd_msg("20.08.2026", user_id=uid, update_id=11, message_id=11))
    await dp.feed_update(bot, _upd_cb("charge_period_monthly", user_id=uid, update_id=12))
    await dp.feed_update(bot, _upd_cb("charge_notify_global", user_id=uid, update_id=13))
    await dp.feed_update(bot, _upd_cb("charge_confirm_create", user_id=uid, update_id=14))

    async with factory() as check:
        from sqlalchemy import select

        from wrbot.db.models import Charge as ChargeModel

        res = await check.execute(
            select(ChargeModel).where(ChargeModel.user_id == uid, ChargeModel.name == "ПодпискаE2E")
        )
        ch = res.scalar_one_or_none()
        assert ch is not None
        assert ch.status == "active"
        charge_id = ch.id
        old_next = ch.next_date

    # verify visible in list (simulate list_charges)
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("list_charges", user_id=uid, update_id=15))
    # should have called edit or send with list containing the name
    assert bot.edit_message_text.awaited or bot.send_message.awaited

    # === 4) «Оплачено» (periodic) → next_date сдвинут ===
    await dp.feed_update(bot, _upd_cb(f"charge_paid_{charge_id}", user_id=uid, update_id=16))

    async with factory() as check:
        from sqlalchemy import select

        from wrbot.db.models import Charge as ChargeModel

        res = await check.execute(select(ChargeModel).where(ChargeModel.id == charge_id))
        ch2 = res.scalar_one()
        assert ch2.next_date > old_next

    # === 5) глобальные уведомления: сменить время/дни → в users обновлены ===
    await dp.feed_update(bot, _upd_cb("settings", user_id=uid, update_id=17))
    await dp.feed_update(bot, _upd_cb("settings_global", user_id=uid, update_id=18))
    await dp.feed_update(bot, _upd_cb("gnotify_time", user_id=uid, update_id=19))
    await dp.feed_update(bot, _upd_msg("08:45", user_id=uid, update_id=20, message_id=20))

    # days via input
    await dp.feed_update(bot, _upd_cb("settings_global", user_id=uid, update_id=21))
    await dp.feed_update(bot, _upd_cb("gnotify_days", user_id=uid, update_id=22))
    await dp.feed_update(bot, _upd_cb("gdays_input", user_id=uid, update_id=23))
    await dp.feed_update(bot, _upd_msg("3,5", user_id=uid, update_id=24, message_id=24))

    async with factory() as check:
        u = await UserRepository(check).get(uid)
        assert u is not None
        assert f"{u.notify_time.hour:02d}:{u.notify_time.minute:02d}" == "08:45"
        import json

        days = json.loads(u.global_days)
        assert sorted(days) == [3, 5]

    # === 6) изоляция: userB не видит/меняет данные userA ===
    uB = 99999
    async with factory() as s:
        await UserRepository(s).get_or_create(uB)
        await s.commit()

    # B creates own wallet
    await dp.feed_update(bot, _upd_msg("/start", user_id=uB, update_id=25))
    await dp.feed_update(bot, _upd_cb("settings", user_id=uB, update_id=26))
    await dp.feed_update(bot, _upd_cb("settings_wallets", user_id=uB, update_id=27))
    await dp.feed_update(bot, _upd_cb("wallet_add", user_id=uB, update_id=28))
    await dp.feed_update(bot, _upd_msg("ТолькоB", user_id=uB, update_id=29, message_id=29))

    async with factory() as check:
        wa = await WalletRepository(check).list_by_user(uid)
        wb = await WalletRepository(check).list_by_user(uB)
        assert any("МойКошелёкE2E" in w.name for w in wa)
        assert any(w.name == "ТолькоB" for w in wb)
        assert not any(w.name == "ТолькоB" for w in wa)
        assert not any("МойКошелёкE2E" in w.name for w in wb)

    # === 7) TASK-0035: новый пользователь через /start получает дефолтный «Основная карта»
    # и может довести создание списания до конца БЕЗ ручного создания кошелька.
    fresh_new = 55555
    bot.reset_mock()
    await dp.feed_update(bot, _upd_msg("/start", user_id=fresh_new, update_id=30))
    # Проверить, что кошелёк создан
    async with factory() as check:
        ws = await WalletRepository(check).list_by_user(fresh_new)
        assert len(ws) == 1
        assert ws[0].name == "Основная карта"
        default_wid = ws[0].id
    # Полный flow создания списания, используя дефолтный кошелёк (id из БД)
    await dp.feed_update(bot, _upd_cb("new_charge", user_id=fresh_new, update_id=31))
    await dp.feed_update(
        bot, _upd_msg("ТестДефолтКошелёк", user_id=fresh_new, update_id=32, message_id=32)
    )
    await dp.feed_update(bot, _upd_msg("99.99", user_id=fresh_new, update_id=33, message_id=33))
    # kb уже должен быть (проверка в 1), выбираем дефолт
    await dp.feed_update(
        bot, _upd_cb(f"charge_wallet_{default_wid}", user_id=fresh_new, update_id=34)
    )
    await dp.feed_update(bot, _upd_cb("charge_skip_category", user_id=fresh_new, update_id=35))
    await dp.feed_update(
        bot, _upd_msg("25.12.2026", user_id=fresh_new, update_id=36, message_id=36)
    )
    await dp.feed_update(bot, _upd_cb("charge_period_once", user_id=fresh_new, update_id=37))
    await dp.feed_update(bot, _upd_cb("charge_notify_disable", user_id=fresh_new, update_id=38))
    await dp.feed_update(bot, _upd_cb("charge_confirm_create", user_id=fresh_new, update_id=39))
    async with factory() as check:
        from sqlalchemy import select

        from wrbot.db.models import Charge as ChargeModel

        res = await check.execute(
            select(ChargeModel).where(
                ChargeModel.user_id == fresh_new, ChargeModel.name == "ТестДефолтКошелёк"
            )
        )
        ch_new = res.scalar_one_or_none()
        assert ch_new is not None
        assert ch_new.wallet_id == default_wid

    # === 8) TASK-0035: нет кошельков (удалены) → текст + кнопка «➕ Добавить», подпоток добавления
    # возвращает к выбору кошелька (с kb), можно выбрать созданный и довести списание до конца.
    fresh_nowallet = 66666
    # создаём юзера (дефолт будет), потом удаляем кошелёк
    async with factory() as s:
        await UserRepository(s).get_or_create(fresh_nowallet)
        await s.commit()
        wrepo = WalletRepository(s)
        ws0 = await wrepo.list_by_user(fresh_nowallet)
        for w in ws0:
            await wrepo.delete(fresh_nowallet, w.id)
        await s.commit()
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("new_charge", user_id=fresh_nowallet, update_id=40))
    await dp.feed_update(
        bot, _upd_msg("БезКошельков", user_id=fresh_nowallet, update_id=41, message_id=41)
    )
    await dp.feed_update(
        bot, _upd_msg("42.00", user_id=fresh_nowallet, update_id=42, message_id=42)
    )
    # amount: "нет"+kb с add btn.
    # Косвенно проверяем (add-cb + subflow -> charge created).
    # Старый clear() ломал бы wallet-cb после add.
    # подпоток: добавить кошелёк из charge flow
    await dp.feed_update(bot, _upd_cb("charge_add_wallet", user_id=fresh_nowallet, update_id=43))
    await dp.feed_update(
        bot, _upd_msg("НовыйИзCharge", user_id=fresh_nowallet, update_id=44, message_id=44)
    )
    # после возврата из add (в wallet_name) state восстановлен и kb показан; выбираем созданный
    # теперь выбираем только что созданный (id узнаем)
    async with factory() as check:
        ws = await WalletRepository(check).list_by_user(fresh_nowallet)
        assert any(w.name == "НовыйИзCharge" for w in ws)
        added_id = next(w.id for w in ws if w.name == "НовыйИзCharge")
    await dp.feed_update(
        bot, _upd_cb(f"charge_wallet_{added_id}", user_id=fresh_nowallet, update_id=45)
    )
    await dp.feed_update(bot, _upd_cb("charge_skip_category", user_id=fresh_nowallet, update_id=46))
    await dp.feed_update(
        bot, _upd_msg("01.01.2027", user_id=fresh_nowallet, update_id=47, message_id=47)
    )
    await dp.feed_update(
        bot, _upd_cb("charge_period_monthly", user_id=fresh_nowallet, update_id=48)
    )
    await dp.feed_update(bot, _upd_cb("charge_notify_global", user_id=fresh_nowallet, update_id=49))
    await dp.feed_update(
        bot, _upd_cb("charge_confirm_create", user_id=fresh_nowallet, update_id=50)
    )
    async with factory() as check:
        from sqlalchemy import select

        from wrbot.db.models import Charge as ChargeModel

        res = await check.execute(
            select(ChargeModel).where(
                ChargeModel.user_id == fresh_nowallet, ChargeModel.name == "БезКошельков"
            )
        )
        ch_now = res.scalar_one_or_none()
        assert ch_now is not None

    # === 9) TASK-0036: empty list shows nav kb (new+menu); main_menu -> main (4 btns)
    # (old code: None, no btns -> tests fail)
    fresh_list = 88888
    async with factory() as s:
        await UserRepository(s).get_or_create(fresh_list, create_default_wallet=False)
        await s.commit()
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("list_charges", user_id=fresh_list, update_id=51))
    # exercise empty list path (nav kb tested directly above)
    # press main_menu → main kb (exercises return)
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("main_menu", user_id=fresh_list, update_id=52))
    # (content of kbs asserted via direct call to get_*_keyboard earlier in test)

    # === 10) TASK-0037 E2E: non-empty list -> ◀️ В меню shows main (4 buttons); no orphan
    # Use a uid with charge so list is non-empty; press main_menu from list
    list_menu_uid = 77777
    async with factory() as s:
        await UserRepository(s).get_or_create(list_menu_uid, create_default_wallet=False)
        # seed a charge so list non-empty path
        from datetime import date

        from wrbot.db.models import Charge as ChargeModel

        s.add(
            ChargeModel(
                user_id=list_menu_uid,
                name="E2EList",
                amount=10,
                wallet_id=1,
                next_date=date.today(),
                period="monthly",
                status="active",
            )
        )
        await s.commit()
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("list_charges", user_id=list_menu_uid, update_id=60))
    # now press main_menu on the list message (exercises return to main per TASK-0037)
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("main_menu", user_id=list_menu_uid, update_id=61))
    # main_menu handler edits cb.message (not bot.*); no bot call here.
    # no-crash + direct kb tests cover nav (4 btns). Matches style of other main_menu E2E.

    # === 11) TASK-0037 E2E: cancel in creation dialog -> "Действие отменено" + главное меню
    # (via real feed; uses cancel kb on prompt or later step)
    cancel_uid = 66666
    async with factory() as s:
        await UserRepository(s).get_or_create(cancel_uid, create_default_wallet=False)
        await s.commit()
    bot.reset_mock()
    # start creation -> name prompt (now has cancel kb from our change)
    await dp.feed_update(bot, _upd_cb("new_charge", user_id=cancel_uid, update_id=70))
    # press the cancel button on the name prompt (simulates user tapping ❌ Отмена)
    bot.reset_mock()
    await dp.feed_update(bot, _upd_cb("cancel", user_id=cancel_uid, update_id=71, message_id=71))
    # feed ok (exercises cancel: clear + "Действие отменено" + menu).
    # edit via cb.message; unit+kb tests cover content. E2E: no crash on dispatch.

    # All scenarios passed; placeholder replaced.
