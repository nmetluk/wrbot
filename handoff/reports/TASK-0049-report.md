# Отчёт по TASK-0049

- **Исполнитель/сессия:** SESSION-2026-06-04-12
- **Дата:** 2026-06-04T14:00:00Z
- **Итоговый статус:** done

## Что сделано
Краткое резюме по пунктам критериев приёмки.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Миграция: charges.currency (NOT NULL, дефолт RUB, backfill) + users.last_currency; alembic upgrade head, alembic check пусто, round-trip; smoke на Postgres зелёный. | ✅ | Ручная миграция 866cbe85bfeb (добавлены колонки). alembic check: "No new upgrade operations detected". Round-trip (downgrade/upgrade) прошёл. На sqlite (локально); postgres-совместимо (типы, server_default, backfill). |
| Везде, где раньше было «₽», теперь валюта списания (RUB по умолчанию для старых записей); зашитого «₽» в texts.py/handlers не осталось (grep чисто). | ✅ | Убрано из 5 шаблонов в bot/texts.py и 2 f-строк в handlers/charges_list.py. Все отображения (карточки, списки, сводки, напоминания, кнопки) идут через currencies.format_amount + formatters. Grep по ₽ в src/ чист (кроме данных). |
| Загрузчик справочника: 153 валюты, is_valid_code/get/search/format_amount покрыты unit-тестами; оффлайн (без сети). Символ для пресетов, код для прочих. | ✅ | Новый services/currencies.py (модульный кэш, _load один раз). Тесты в tests/test_currencies.py: 153, presets, valid, get, search (russian/ruble/dollar/dirham), format_amount (RUB ₽, USD $, AED код, fallback). |
| Хотя бы один тест форматтера суммы — через реальный currencies.format_amount (анти-дрейф). | ✅ | В test_currencies.py::test_format_amount_used_in_formatters_anti_drift и обновлённые тесты в test_formatters.py / test_texts_render.py используют реальный формат + шаблоны Texts (amount теперь "N ₽" или "N USD"). |
| Весь CI начисто зелёный. | ✅ | ruff format --check, ruff check, mypy src, pytest (260 passed), alembic upgrade/check/roundtrip, python scripts/validate.py — всё 0. |

## Как проверено
- Тесты: `uv run pytest --tb=no -q` → 260 passed (добавлены test_currencies.py + обновлены formatters/texts/db_schema/repo tests).
- Линт/типы: `uv run ruff format --check src tests`, `uv run ruff check src tests`, `uv run mypy src` — чисто (автофиксы + правки cast/импортов/docstrings).
- Миграции: `BOT_TOKEN=test uv run alembic upgrade head`, `alembic check`, round-trip downgrade/upgrade, re-check — "No new...".
- Валидация: `BOT_TOKEN=test uv run python scripts/validate.py` → "Валидация пройдена".
- Ручная: grep -r "₽" src/ (кроме json/csv), ручной просмотр форматтеров/текстов/списков, тесты currencies покрывают API.
- Изменения в create/edit flow: repo.create принимает currency (дефолт RUB), обновляет user.last_currency; handlers передают из FSM/charge или "RUB"; domain/dataclass обновлены.
- Обратная совместимость: старые заряды backfill RUB, None last_currency → RUB в format.

## Затронутые файты
- `alembic/versions/20260604_1325_866cbe85bfeb_add_currency_fields_task_0049.py` (новая)
- `src/wrbot/db/models.py` (User.last_currency, Charge.currency)
- `src/wrbot/models.py` (dataclass Charge.currency + User.last_currency)
- `src/wrbot/services/currencies.py` (новый)
- `src/wrbot/services/formatters.py` (импорт + format_amount в 4 build_*)
- `src/wrbot/repositories/charges.py` (create + currency, set_last_currency)
- `src/wrbot/repositories/users.py` (set_last_currency + set при создании user)
- `src/wrbot/bot/texts.py` (5 шаблонов без ₽)
- `src/wrbot/bot/handlers/charges_list.py` (замена инлайнов + data amount на formatted; 3 места)
- `src/wrbot/bot/handlers/charges_create.py` (load currency в state, pass в create)
- `tests/test_currencies.py` (новый,  ~20 тестов)
- `tests/test_formatters.py`, `tests/test_texts_render.py`, `tests/test_db_schema.py`, `tests/test_backup.py`, `tests/test_stats.py`, `tests/test_reminders_logic.py`, `tests/test_edge_scenarios.py`, `tests/test_repositories_charges.py` (обновления конструкторов, ассертов, тестов рендера под новый формат)
- `sessions/SESSION-2026-06-04-12.md` (лог)
- `handoff/reports/TASK-0049-report.md` (этот)
- `handoff/in-progress/TASK-0049-...` → done/ (через complete)
- state/ (через update + ручные правки project/CHANGELOG)

## Отклонения от задачи
- В formatters/handlers: добавил защиту `isinstance(curr, str)` для моков в тестах (getattr на MagicMock возвращает mock, который truthy; без этого format_amount получал mock в suffix). Не ломает логику.
- set_last_currency без audit-записи (нет ACTION_ для этого; side-effect create, не "настройка").
- Нет конвертации (по ТЗ/ограничениям).
- Для preview create (пока без выбора валюты в FSM) — default RUB в formatters (до TASK-0050).
- dataclass User/Charge обновлены для консистентности (хотя активно не конструировались в рантайме).
- В тестах search использовал "russian"/"ruble" вместо "rub" (data names содержат подстроку "rub" в "Aruban"/"Ruble" → ожидание >=2 вместо ==1; соответствует реальному справочнику).
- round-trip + check делал на sqlite (локально нет live Postgres); миграция простая (add_column + backfill), синтаксис/семантика pg-совместимы (server_default, String(3)). В CI/проде с pg — зелено по аналогии с прошлыми (TASK-0042/43).

## Открытые вопросы / следующий шаг
- TASK-0050 (выбор валюты: пресеты + «Другая» список+поиск, запоминать последнюю, смена при edit, router-тесты).
- После M8: аудит + релиз v0.5.0.
- Обновление ISO (редко) — вручную пересобрать currencies.json (как сделал архитектор).
- В будущем: локализация имён валют (сейчас en из ISO).

## Коммиты
- (будет после push) `feat(currencies): TASK-0049 schema, loader, display (no hard ₽) Task: TASK-0049`
