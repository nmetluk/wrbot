"""
Форматтеры отображения для списаний (TASK-0039).

- format_date_ru: ДД.ММ.ГГГГ
- format_period_ru: человекочитаемый период
- format_*_notify: глобальные / свои: ... / отключены
- Резолв имён кошелька/категории через репозитории (не ID и не хардкод в UI)
- build_* для сводки и карточки

Все пользовательские строки — через Texts (без хардкода в сервисах/хэндлерах).
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING, Any

from wrbot.bot.texts import Texts
from wrbot.repositories.categories import CategoryRepository
from wrbot.repositories.wallets import WalletRepository
from wrbot.services import currencies

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def format_date_ru(d: date | str | None) -> str:
    """Формат ДД.ММ.ГГГГ. Поддержка str (iso) для данных FSM."""
    if d is None:
        return "?"
    if isinstance(d, str):
        try:
            parsed = date.fromisoformat(d)
            return parsed.strftime("%d.%m.%Y")
        except Exception:
            return d  # fallback на сырое, если не iso
    return d.strftime("%d.%m.%Y")


def format_period_ru(period: str | None) -> str:
    """Единый маппинг периодов (вынос из дублирующихся _format_period)."""
    mapping = {
        "once": "одноразово",
        "monthly": "ежемесячно",
        "quarterly": "ежеквартально",
        "yearly": "ежегодно",
    }
    if not period:
        return "?"
    return mapping.get(period, period)


def format_notify_from_fsm(notify_data: dict[str, Any] | None) -> str:
    """Для превью сводки при создании/редактировании (FSM data)."""
    if not notify_data:
        return Texts.notify_global
    ntype = notify_data.get("type")
    if ntype == "disabled" or notify_data.get("disabled"):
        return Texts.notify_disabled
    days = notify_data.get("days")
    if days:
        days_str = ", ".join(map(str, days))
        return Texts.notify_custom.format(days=days_str)
    return Texts.notify_global


def format_notify_for_charge(charge: Any) -> str:
    """
    Для карточки/списка по сохранённому заряду.

    Использует charge.individual_days (JSON-строка или None).
    None/отсутствие -> глобальные (как дефолт).
    [] -> отключены.
    [1,3,5] -> свои: 1, 3, 5
    """
    ind = getattr(charge, "individual_days", None)
    if ind:
        try:
            days = json.loads(ind)
            if isinstance(days, list):
                if len(days) == 0:
                    return Texts.notify_disabled
                days_str = ", ".join(map(str, sorted(int(d) for d in days if str(d).strip())))
                return Texts.notify_custom.format(days=days_str)
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
            pass
    return Texts.notify_global


async def resolve_wallet_name(session: AsyncSession, user_id: int, wallet_id: int | None) -> str:
    """Имя кошелька (с иконкой) через репозиторий. Иконка: TASK-0042."""
    if wallet_id is None:
        return "?"
    repo = WalletRepository(session)
    w = await repo.get(user_id, wallet_id)
    if w and getattr(w, "name", None):
        icon = getattr(w, "icon", None) or "👛"
        return f"{icon} {w.name}"
    return f"ID {wallet_id}"


async def resolve_category_name(
    session: AsyncSession, user_id: int, category_id: int | None
) -> str:
    """Имя категории или «—» если пропущена."""
    if category_id is None:
        return Texts.category_skipped
    repo = CategoryRepository(session)
    c = await repo.get(user_id, category_id)
    if c and getattr(c, "name", None):
        return c.name
    return f"ID {category_id}"


async def build_new_charge_summary(
    session: AsyncSession, user_id: int, data: dict[str, Any]
) -> str:
    """Сводка перед подтверждением создания/правки списания (замена _build_summary_text)."""
    wallet = await resolve_wallet_name(session, user_id, data.get("wallet_id"))
    category = await resolve_category_name(session, user_id, data.get("category_id"))
    next_date = format_date_ru(data.get("next_date"))
    period = format_period_ru(data.get("period"))
    notify = format_notify_from_fsm(data.get("notify"))

    amount_raw = data.get("amount", "?")
    curr = data.get("currency")
    curr = curr if isinstance(curr, str) else currencies.get_default()
    formatted_amount = currencies.format_amount(amount_raw, curr)

    return Texts.new_charge_summary.format(
        name=data.get("name", "?"),
        amount=formatted_amount,
        wallet=wallet,
        category=category,
        next_date=next_date,
        period=period,
        notify=notify,
    )


async def build_charge_card_text(session: AsyncSession, user_id: int, charge: Any) -> str:
    """Полная карточка списания (замена заглушек в show_charge_card)."""
    wallet = await resolve_wallet_name(session, user_id, getattr(charge, "wallet_id", None))
    category = await resolve_category_name(session, user_id, getattr(charge, "category_id", None))
    next_date = format_date_ru(getattr(charge, "next_date", None))
    period = format_period_ru(getattr(charge, "period", None))
    notify = format_notify_for_charge(charge)

    amount_raw = getattr(charge, "amount", "?")
    curr = getattr(charge, "currency", None)
    curr = curr if isinstance(curr, str) else currencies.get_default()
    formatted_amount = currencies.format_amount(amount_raw, curr)

    return Texts.my_charges_card.format(
        name=getattr(charge, "name", "?"),
        amount=formatted_amount,
        wallet=wallet,
        category=category,
        next_date=next_date,
        period=period,
        notify=notify,
    )


def format_charge_button_text(name: str, amount: str, wallet: str, next_date: str) -> str:
    """Для кнопок в списке «Мои списания» (с wallet + ДД.ММ)."""
    return Texts.my_charges_button.format(
        name=name, amount=amount, wallet=wallet, next_date=next_date
    )


async def build_reminder_text(session: AsyncSession, user_id: int, charge: Any) -> str:
    """Текст push-уведомления (reminder_notification) с реальным кошельком и ДД.ММ.ГГГГ."""
    wallet = await resolve_wallet_name(session, user_id, getattr(charge, "wallet_id", None))
    next_date = format_date_ru(getattr(charge, "next_date", None))

    amount_raw = getattr(charge, "amount", "?")
    curr = getattr(charge, "currency", None)
    curr = curr if isinstance(curr, str) else currencies.get_default()
    formatted_amount = currencies.format_amount(amount_raw, curr)

    return Texts.reminder_notification.format(
        name=getattr(charge, "name", "?"),
        amount=formatted_amount,
        wallet=wallet,
        next_date=next_date,
    )


async def build_edit_live_card(
    session: AsyncSession, user_id: int, data: dict[str, Any], step: str
) -> str:
    """Живая карточка редактирования (TASK-0045): текущие (подтверждённые) данные + текущий шаг."""
    base = await build_new_charge_summary(session, user_id, data)
    step_labels = {
        "name": "название",
        "amount": "сумма",
        "wallet": "кошелёк",
        "category": "категория",
        "period": "период",
        "next_date": "дата (ДД.ММ.ГГГГ)",
        "notify": "уведомления",
    }
    label = step_labels.get(step, step)
    return base + f"\n\n✏️ Редактирование шага: {label}\nВведите значение или выберите кнопку."
