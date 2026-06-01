---
id: TASK-0019
title: "Переносимый идемпотентный record() в SentReminderRepository (SQLite+PostgreSQL)"
milestone: M4
status: inbox
priority: medium
created_by: architect
created_at: 2026-06-01T21:30:00Z
depends_on: [TASK-0014]
---

# TASK-0019: Переносимая идемпотентная запись sent_reminders

## Цель
Убрать SQLite-only `INSERT OR IGNORE` из `SentReminderRepository.record`, чтобы код
работал и на PostgreSQL (путь по ADR-0003).

## Контекст / приоритет
- **Severity: major (переносимость).** Найдено в AUDIT-M4. Для v1 (SQLite) работает, но
  на PostgreSQL `dialects.sqlite.insert(...).prefix_with("OR IGNORE")` даст невалидный SQL.
- ADR-0003 (SQLite→PostgreSQL без переписывания слоя данных).

## Критерии приёмки (проверяемые)
- [ ] `record(...)` идемпотентен и **диалект-независим**. Варианты: (а) dialect-aware
      `on_conflict_do_nothing` (SQLite `insert().on_conflict_do_nothing` и PG-аналог по
      UNIQUE `uq_reminder`), либо (б) проверка `was_sent` + INSERT с перехватом `IntegrityError`.
      Не использовать `prefix_with("OR IGNORE")`.
- [ ] Тест идемпотентности проходит на SQLite (двойной `record` → одна строка, без исключения).
- [ ] (Если разумно) комментарий/тест-маркер, что поведение совместимо с PostgreSQL ON CONFLICT.
- [ ] Весь CI начисто без BOT_TOKEN зелёный (ruff format/check, mypy, pytest, alembic, validate).

## Ожидаемые артефакты
- Код: `src/wrbot/repositories/sent_reminders.py`.
- Тесты: `tests/test_repositories_sent_reminders.py` (идемпотентность).

## Ограничения / заметки
- Не блокирует v1-рантайм (SQLite), но желательно закрыть до перехода на PostgreSQL (M5/деплой).
- Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0014
