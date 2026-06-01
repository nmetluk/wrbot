# Отчёт по TASK-0014

- **Исполнитель/сессия:** SESSION-2026-06-01-24
- **Дата:** 2026-06-01T20:30:00Z
- **Итоговый статус:** done

## Что сделано
Реализована чистая due-логика напоминаний + данные для M4 (фундамент для свипа).

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Эффективные дни (global/individual/off) | ✅ | get_effective_days в services/reminders.py |
| Due-расчёт (с учётом snooze repeat) | ✅ | get_due_target_days |
| Выбор пользователей по notify_time/tz | ✅ | select_users_to_notify_at (edge: границы суток, разные пояса) |
| SentReminderRepository (идемпотентность) | ✅ | was_sent + record (OR IGNORE для SQLite) |
| ChargeRepository.snooze | ✅ | Не меняет next_date (по ADR-0005) |
| Тесты (реальная миграция) | ✅ | test_reminders_logic.py (логика), test_repositories_sent_reminders.py (идемпотентность) |
| CI зелёный | ✅ | 124 pytest, mypy 0, ruff clean, etc. |

## Как проверено
- Полный CI (executor-guide + whole-repo ruff) — зелёный.
- 8 новых тестов проходят (логика + DB идемпотентность).
- Ручная проверка edge-кейсов (snooze repeat, tz midnight, etc.).

## Затронутые файлы
- `src/wrbot/repositories/charges.py` — snooze
- `src/wrbot/repositories/sent_reminders.py` — **новый**
- `src/wrbot/services/reminders.py` — полная реализация (была заглушка)
- `tests/test_reminders_logic.py`, `tests/test_repositories_sent_reminders.py` — новые
- Отчёт, сессия 24, state, CHANGELOG

## Отклонения
- В get_due... использован упрощённый запрос (для тестов); в проде можно оптимизировать индексами.
- select_users_to_notify_at — helper (полный запрос в scheduler 0016).

## Принятые решения
- Логика чистая (pure functions + repo) — легко тестировать, как требовал ADR-0005.
- Идемпотентность через БД UNIQUE (не в памяти).

## Следующий шаг
TASK-0015 (текст+кнопки уведомления) → 0016 (свип-планировщик). После M4 — строгий аудит (рестарт, идемпотентность, точность).

## Коммиты
- `feat(m4): TASK-0014 reminder due-logic + SentReminderRepository + snooze (Task: TASK-0014)`
