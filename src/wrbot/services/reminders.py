"""
Reminder calculation logic.

Функции для определения кому/когда/за сколько дней присылать напоминания.
"""

from datetime import date

# TODO: M3 - реализовать расчёт напоминаний:
# - get_active_reminders(): получить все заряды с напоминаниями на сегодня
# - check_should_remind(): проверить нужно ли присылать напоминание
# с учётом snoozed_until, individual_days, global_days


def get_reminder_dates(target_date: date, days: list[int]) -> list[date]:
    """Получить даты напоминаний для указанной даты."""
    return [target_date]  # заглушка
