"""
Reminder calculation logic (M4).

Чистые функции + интеграция с репозиториями для due-расчёта напоминаний.
Все времена в UTC. Соответствует ADR-0005.
"""

import json
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from wrbot.db.models import Charge, User
from wrbot.repositories.sent_reminders import SentReminderRepository

logger = logging.getLogger(__name__)


def get_effective_days(charge: Charge, user: User | None = None) -> list[int]:
    """
    Возвращает действующий набор дней напоминаний для списания.

    - Если у charge.individual_days задан (не None и не [] ) — используем его.
    - Иначе global_days пользователя.
    - [] = напоминания отключены.
    """
    if charge.individual_days is not None:
        try:
            days = json.loads(charge.individual_days)
            if isinstance(days, list) and len(days) > 0:
                return sorted({int(d) for d in days if isinstance(d, (int, str))})
            elif days == []:
                return []
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    if user and user.global_days:
        try:
            days = json.loads(user.global_days)
            if isinstance(days, list):
                return sorted({int(d) for d in days if isinstance(d, (int, str))})
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    # Default fallback (should not happen in practice)
    return [5, 3, 1]


def get_due_target_days(
    charge: Charge, today: date, user: User | None = None
) -> list[tuple[date, int]]:
    """
    Для данного списания и даты 'today' возвращает список (target_date, days_before)
    для которых должно сработать напоминание сегодня.

    Учитывает snoozed_until: если snoozed_until == today — повторное напоминание
    (даже если уже было отправлено за эти дни; логика идемпотентности выше).
    """
    effective_days = get_effective_days(charge, user)
    if not effective_days:
        return []

    due = []
    for days_before in effective_days:
        target = charge.next_date - timedelta(days=days_before)
        if target == today:
            # Обычное срабатывание
            due.append((target, days_before))

    # Snooze repeat: если snoozed_until == today, добавляем повтор для всех effective дней
    # (в реальности сработает только то, что не было отправлено, но для полноты логики)
    if charge.snoozed_until and charge.snoozed_until == today:
        for days_before in effective_days:
            target = charge.next_date - timedelta(days=days_before)
            if (target, days_before) not in due:
                due.append((target, days_before))

    return sorted(due)


async def select_users_to_notify_at(session: AsyncSession, now_utc: datetime) -> list[User]:
    """
    Выбрать пользователей, у которых прямо сейчас (в их часовом поясе) наступило
    их notify_time (с точностью до минуты).

    Используется свипом (scheduler) для определения, кого опрашивать в текущий тик.
    """
    # В реальной реализации — запрос к БД с фильтром.
    # Здесь заглушка для чистой логики; в проде будет в репозитории или сервисе.
    # Для тестов достаточно.
    from sqlalchemy import select

    result = await session.execute(select(User))
    users = result.scalars().all()

    to_notify = []
    for user in users:
        try:
            tz = ZoneInfo(user.tz)
            local_now = now_utc.astimezone(tz)
            local_time = local_now.time().replace(second=0, microsecond=0)
            user_notify = user.notify_time.replace(second=0, microsecond=0)
            if local_time == user_notify:
                to_notify.append(user)
        except Exception as e:
            logger.warning("Bad tz for user %s: %s", user.tg_id, e)

    return to_notify


async def get_due_reminders_today(
    session: AsyncSession,
    today: date,
    sent_repo: SentReminderRepository,
) -> list[dict[str, object]]:
    """
    Главная функция для свипа: вернуть что нужно отправить сегодня.

    Возвращает список словарей с информацией для отправки (charge, user, days_before, target_date).
    """
    from sqlalchemy import select

    # Получить активные charges с пользователями (join)
    stmt = (
        select(Charge, User)
        .join(User, Charge.user_id == User.tg_id)
        .where(Charge.status == "active")
    )
    result = await session.execute(stmt)
    rows = result.all()

    due_to_send = []

    for charge, user in rows:
        if charge.snoozed_until and charge.snoozed_until > today:
            continue  # пока отложено

        due_pairs = get_due_target_days(charge, today, user)
        for target_date, days_before in due_pairs:
            if await sent_repo.was_sent(charge.id, target_date, days_before):
                continue  # уже отправлено (идемпотентно)

            due_to_send.append(
                {
                    "charge": charge,
                    "user": user,
                    "target_date": target_date,
                    "days_before": days_before,
                    "effective_days": get_effective_days(charge, user),
                }
            )

    return due_to_send
