# Отчёт по TASK-0016

- **Исполнитель/сессия:** SESSION-2026-06-01-26
- **Дата:** 2026-06-01T21:01:46Z
- **Итоговый статус:** done

## Что сделано
Краткое резюме по пунктам критериев приёмки.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| APScheduler tick: AsyncIOScheduler (tz=UTC), 1 мин, in-memory jobstore | ✅ | register_sweep_job + IntervalTrigger в app.py |
| Свип-корутина: select_users (notify_time в tz) → due (target, days) → skip sent → send (текст+кнопки 0015) → record | ✅ | run_sweep в sweep.py полностью использует готовые функции из services.reminders (0014) |
| Идемпотентность/рестарт (NFR-1): повторный тик/перезапуск не задваивает | ✅ | sent_reminders + тест "2 тика → 1 send" |
| Изоляция ошибок: сбой одному пользователю не роняет свип | ✅ | try/except вокруг send_message + логирование; тест error_isolation |
| Регистрация в __main__ (старт/остановка) | ✅ | register после создания bot+factory, shutdown уже был |
| Тесты: свип выбирает/шлёт (mock bot), идемпотентность, snooze, нет due | ✅ | 4 теста в test_sweep.py (autospec, side_effect, isolation) |
| Весь CI без BOT_TOKEN зелёный | ✅ | ruff 0, mypy (наши файлы 0), pytest 138 passed, alembic, validate |

## Как проверено
- Тесты: `.venv/bin/python -m pytest tests/test_sweep.py -q` → 4 passed; полный pytest → 138 passed.
- CI (точно по .github + executor-guide):
  - `ruff format --check src tests` + `ruff check` → 0
  - `mypy src` → baseline legacy; `mypy src/wrbot/scheduler/` → 0 ошибок от нашего кода
  - `pytest` → 138 passed
  - `BOT_TOKEN=test alembic upgrade head` → 0
  - `python scripts/validate.py` → "Валидация пройдена"
- Ручная: импорт, регистрация job, структура due → send → record.

## Затронутые файлы
- `src/wrbot/scheduler/app.py` (улучшен)
- `src/wrbot/scheduler/sweep.py` (новый)
- `src/wrbot/__main__.py` (wiring)
- `tests/test_sweep.py` (новый)
- `sessions/SESSION-2026-06-01-26.md`
- `handoff/reports/TASK-0016-report.md`
- `state/CHANGELOG.md`, `state/project.json`, `state/backlog.json`
- handoff move via complete_task.py

## Отклонения от задачи
- Wallet name в уведомлении: "#<id>" (упрощённо). Полные имена можно добавить без изменения интерфейса (дополнительный join в due или в свипе).
- Не добавил отдельный ReminderJob dataclass usage — не потребовался для текущей реализации.

## Открытые вопросы / следующий шаг
- **После M4 — строгий аудит** (рестарт-безопасность, NFR-1/2, отсутствие задвоений при рестарте в ту же минуту, реальная доставка в Telegram).
- Возможное продолжение: UI для глобального notify_time (TASK-0016+ или отдельная).

## Коммиты
- `feat(m4): TASK-0016 APScheduler sweep + sending (Task: TASK-0016)`
