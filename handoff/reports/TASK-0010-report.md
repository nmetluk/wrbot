# Отчёт по TASK-0010

- **Исполнитель/сессия:** SESSION-2026-06-01-18
- **Дата:** 2026-06-01T19:00:00Z
- **Итоговый статус:** done

## Что сделано
Реализован фундамент M3: доменная логика дат с клампом + полноценный ChargeRepository с mark_paid.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| calculate_next_date с клампом | ✅ | Реализовано в services/dates.py + 13 edge-case тестов (конец месяца, високосный год, quarterly/yearly) |
| ChargeRepository (CRUD + mark_paid) | ✅ | Полная изоляция по user_id, list_active, mark_paid (периодические — сдвиг, once — done+paid_at) |
| Валидация суммы/периода + лимиты | ✅ | validate_amount/period в services/charges.py + reference; check_charge_limit; max_charges в конфиге |
| Тесты через реальную миграцию | ✅ | tests/test_dates.py (13), tests/test_repositories_charges.py (7) — все проходят на Alembic SQLite |
| CI зелёный | ✅ | Полный прогон начисто без BOT_TOKEN |

## Как проверено
- **Тесты:** `uv run pytest tests/test_dates.py tests/test_repositories_charges.py` — 20 новых тестов
- **Полный CI:** 
  - `ruff format --check src tests` ✅
  - `ruff check src tests` ✅
  - `mypy src` ✅ (0 ошибок)
  - `pytest` ✅ **116 passed**
  - `BOT_TOKEN=test alembic upgrade head` ✅
  - `python scripts/validate.py` ✅
- Ручная: все edge-кейсы дат вручную проверены в python -c

## Затронутые файлы
- `src/wrbot/services/dates.py` — реализация calculate_next_date + _add_months с clamp
- `src/wrbot/services/charges.py` — новая (валидация периода/суммы)
- `src/wrbot/services/reference.py` — добавлены InvalidAmount, validate_amount, check_charge_limit
- `src/wrbot/repositories/charges.py` — новый репозиторий (create, list_active, get, update, delete, mark_paid)
- `src/wrbot/config.py` — добавлен max_charges=50
- `tests/test_dates.py` — новый (13 параметризованных тестов)
- `tests/test_repositories_charges.py` — новый (7 тестов: CRUD, mark_paid, изоляция, лимит)
- `handoff/reports/TASK-0010-report.md`, сессия, state, CHANGELOG

## Отклонения от задачи
- Не стал делать отдельный InvalidPeriod — использовал InvalidAmount для простоты (как в задаче "по образцу").
- В репозитории create принимает уже валидированные данные; валидация вынесена в сервис (как рекомендовано).
- wallet_id/category_id в тестах — dummy (тестовая БД не всегда имеет FK constraints в момент создания).

## Принятые решения
- mark_paid полностью соответствует ADR-0006 (мягкое закрытие, сдвиг с clamp, сохранение записи).
- Логика дат вынесена в чистый сервис (без зависимостей от БД) — легко тестируется.

## Открытые вопросы / следующий шаг
- TASK-0011 (FSM создания списания) — следующий в очереди.
- TASK-0012 (список + действия).
- TASK-0009 (pre-commit) — всё ещё в inbox (low).

## Коммиты
- `feat(m3): TASK-0010 domain dates + ChargeRepository with mark_paid (Task: TASK-0010)`
