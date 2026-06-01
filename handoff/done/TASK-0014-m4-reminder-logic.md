---
id: TASK-0014
title: "M4: логика напоминаний (due-расчёт) + SentReminderRepository + snooze"
milestone: M4
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T20:00:00Z
depends_on: [TASK-0012]
---

# TASK-0014: Логика напоминаний + данные (фундамент M4)

## Цель
Заложить чистую, тестируемую логику «какие напоминания должны уйти» и данные для
идемпотентности. **Без APScheduler и без отправки в Telegram** (это TASK-0015/0016).

## Контекст
- ТЗ §3.4 (дни напоминаний, глобальные/индивидуальные), §2.
- Требования: FR-10, FR-11, FR-13; NFR-2 (точность).
- ADR: **ADR-0005** (свип по БД + `sent_reminders` UNIQUE(charge_id,target_date,days_before);
  «Отложить» не меняет `next_date`; метки UTC), ADR-0004 (tz/UTC), ADR-0006 (даты).
- Готово: модели `Charge`/`SentReminder`/`User`; `ChargeRepository`; `services/reminders.py` (заглушка).
  Таблица `sent_reminders` уже в схеме (миграция не нужна).

## Критерии приёмки (проверяемые)
- [ ] **Эффективные дни (FR-11):** функция возвращает действующий набор дней для списания:
      `individual_days` если не `null`, иначе `global_days`; `[]` = напоминания выключены.
- [ ] **Due-расчёт:** по `charge.next_date` и набору дней — какие `(target_date, days_before)`
      «срабатывают сегодня» (т.е. `next_date - days_before == today`). Плюс учёт `snoozed_until`:
      если `snoozed_until == today` — повторное напоминание должно сработать (ADR-0005),
      не двигая `next_date`.
- [ ] **Выбор пользователей по времени (чистый helper):** для данного UTC-момента (час:минута)
      определить, у каких пользователей сейчас наступило их `notify_time` в их `tz` (ADR-0004).
      Покрыто тестами на разные пояса и границу суток/минуты (NFR-2 ±1 мин).
- [ ] **SentReminderRepository:** `was_sent(charge_id, target_date, days_before) -> bool`,
      `record(...)` — идемпотентная вставка (UNIQUE защищает от дублей; повтор не падает/не задваивает).
- [ ] **`ChargeRepository.snooze(user_id, charge_id, until: date)`** — ставит `snoozed_until`,
      `next_date` НЕ меняет (ADR-0005); изоляция по `user_id`.
- [ ] **Тесты** (через реальную миграцию, где нужно БД): эффективные дни (global/individual/off),
      due на границах (за 5/3/1 день, не-срабатывание), snooze-повтор, выбор по tz/времени,
      идемпотентность `record`/`was_sent`. Моки со `spec`/autospec.
- [ ] Весь CI начисто без BOT_TOKEN зелёный (ruff format/check, mypy, pytest, alembic, validate).

## Ожидаемые артефакты
- Код: `src/wrbot/services/reminders.py` (реализация), `src/wrbot/repositories/sent_reminders.py`,
  `ChargeRepository.snooze`.
- Тесты: `tests/test_reminders_logic.py`, `tests/test_repositories_sent_reminders.py`.

## Ограничения / заметки
- Без планировщика и без `bot.send_message` (TASK-0015/0016). Чистая логика + данные.
- Все метки времени — UTC. Перед `done`: полный CI (executor-guide), отчёт, лог, push.

## Зависимости
Зависит от: TASK-0012
