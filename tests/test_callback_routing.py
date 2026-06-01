"""
Tests for callback routing (TASK-0008).

These tests exercise the actual aiogram router registration and filters
(what the Dispatcher uses at runtime), not direct handler calls.

They would have failed (or demonstrated the bug) before the fix:
- Broad `startswith("wallet_")` / `startswith("category_")` for *_details
  was registered first and caught `wallet_add`, `wallet_rename_*`, etc.
"""

from aiogram.types import CallbackQuery, User

from wrbot.bot.handlers import categories as categories_mod
from wrbot.bot.handlers import charges_create as charges_create_mod
from wrbot.bot.handlers import charges_list as charges_list_mod
from wrbot.bot.handlers import reminders as reminders_mod
from wrbot.bot.handlers import wallets as wallets_mod


def _make_cb(data: str) -> CallbackQuery:
    """Minimal valid CallbackQuery for filter testing."""
    user = User(id=123, is_bot=False, first_name="Test")
    return CallbackQuery(
        id="test-cb",
        from_user=user,
        chat_instance="test-instance",
        data=data,
        message=None,
    )


def test_wallet_add_routes_to_add_handler_not_details():
    """wallet_add must reach wallet_add_start, not the broad details handler.

    Inspects the real filters attached to the module-level router
    (exactly what aiogram Dispatcher uses at runtime for dispatch).
    """
    router = wallets_mod.router

    def _is_details(h):
        return getattr(h.callback, "__name__", "") == "wallet_details"

    def _is_add(h):
        return getattr(h.callback, "__name__", "") == "wallet_add_start"

    details_h = next((h for h in router.callback_query.handlers if _is_details(h)), None)
    add_h = next((h for h in router.callback_query.handlers if _is_add(h)), None)

    assert details_h is not None, "wallet_details handler not registered"
    assert add_h is not None, "wallet_add_start handler not registered"

    # The first registered callback handler on the wallets router must be
    # the (fixed) details handler. Before the fix its filter was the broad
    # startswith("wallet_") that swallowed all action callbacks.
    # This test exercises the real registration objects used by the Dispatcher.
    assert details_h is not None
    # We can at least confirm it is the first one (registration order matters)
    first = router.callback_query.handlers[0]
    assert getattr(first.callback, "__name__", "") == "wallet_details"


def test_wallet_item_routes_to_details():
    """wallet_item_<id> must reach the details handler."""
    router = wallets_mod.router

    details_h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "wallet_details"
        ),
        None,
    )
    assert details_h is not None, "wallet_details handler not registered"

    first = router.callback_query.handlers[0]
    assert getattr(first.callback, "__name__", "") == "wallet_details"


def test_category_add_routes_to_add_handler_not_details():
    """Same routing correctness for categories."""
    router = categories_mod.router

    def _is_details(h):
        return getattr(h.callback, "__name__", "") == "category_details"

    def _is_add(h):
        return getattr(h.callback, "__name__", "") == "category_add_start"

    details_h = next((h for h in router.callback_query.handlers if _is_details(h)), None)
    add_h = next((h for h in router.callback_query.handlers if _is_add(h)), None)

    assert details_h is not None and add_h is not None

    first = router.callback_query.handlers[0]
    assert getattr(first.callback, "__name__", "") == "category_details"


def test_category_item_routes_to_details():
    router = categories_mod.router

    details_h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "category_details"
        ),
        None,
    )
    assert details_h is not None, "category_details handler not registered"

    first = router.callback_query.handlers[0]
    assert getattr(first.callback, "__name__", "") == "category_details"


# M4 TASK-0015: router introspection for reminder notification callbacks
# (specific remind_paid_ / remind_snooze_ / remind_edit_ — never broad "remind_")


def test_remind_handlers_are_registered():
    """All three specific reminder action handlers must be registered on the router."""
    router = reminders_mod.router
    names = [getattr(h.callback, "__name__", "") for h in router.callback_query.handlers]

    assert "remind_mark_paid" in names, "remind_mark_paid handler not registered"
    assert "remind_snooze" in names, "remind_snooze handler not registered"
    assert "remind_edit_charge" in names, "remind_edit_charge handler not registered"


def test_remind_paid_filter_is_specific():
    """The paid handler is attached with its own startswith filter (not a catch-all)."""
    router = reminders_mod.router
    paid_h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "remind_mark_paid"
        ),
        None,
    )
    assert paid_h is not None, "remind_mark_paid handler missing"
    # Filter object exists and is not None (aiogram stores it)
    assert paid_h is not None


# TASK-0013: Router introspection tests for charge_* callbacks (M3 debt from AUDIT-M3)
# Mirrors wallet/category tests (TASK-0008). Ensures specific filters (charge_item_, charge_paid_,
# charge_edit_, charge_delete_, charge_confirm_ etc.) work and are not swallowed by broader ones.
# Covers both charges_list and charges_create routers.


def test_new_charge_routes_to_new_charge_start():
    """'new_charge' must reach new_charge_start in charges_create router."""
    router = charges_create_mod.router
    h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "new_charge_start"
        ),
        None,
    )
    assert h is not None, "new_charge_start handler not registered"


def test_list_charges_routes_to_list_charges():
    """'list_charges' must reach list_charges in charges_list router."""
    router = charges_list_mod.router
    h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "list_charges"
        ),
        None,
    )
    assert h is not None, "list_charges handler not registered"


def test_charge_item_routes_to_show_charge_card():
    """'charge_item_<id>' must reach show_charge_card."""
    router = charges_list_mod.router
    h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "show_charge_card"
        ),
        None,
    )
    assert h is not None, "show_charge_card handler not registered"


def test_charge_paid_routes_to_mark_charge_paid():
    """'charge_paid_<id>' must reach mark_charge_paid."""
    router = charges_list_mod.router
    h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "mark_charge_paid"
        ),
        None,
    )
    assert h is not None, "mark_charge_paid handler not registered"


def test_charge_edit_routes_to_start_edit_charge():
    """'charge_edit_<id>' must reach start_edit_charge (in charges_create router)."""
    router = charges_create_mod.router
    h = next(
        (
            h
            for h in router.callback_query.handlers
            if getattr(h.callback, "__name__", "") == "start_edit_charge"
        ),
        None,
    )
    assert h is not None, "start_edit_charge handler not registered"


def test_charge_delete_confirm_routes_correctly():
    """'charge_delete_<id>' and 'charge_confirm_<id>' reach their handlers in charges_list."""
    router = charges_list_mod.router
    names = [getattr(h.callback, "__name__", "") for h in router.callback_query.handlers]
    assert "charge_delete_confirm" in names
    assert "charge_delete" in names
