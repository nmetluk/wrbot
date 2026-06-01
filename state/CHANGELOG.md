# Project Session Changelog

Журнал сессий и изменений проекта wrbot. Даты в UTC.

**Назначение:** Этот файл — машиночитаемый журнал сессий, каждый шаг разработки.
Для пользователей см. `/CHANGELOG.md` (история версий).

## [Unreleased]

### Done (M5 start)
- **TASK-0020 (executor, SESSION-2026-06-01-34):** ✅ детерминированный CI — `.github/workflows/ci.yml` переведён на `uv sync --frozen --extra dev` + все гейты через `uv run`. Обновлены инструкции в `executor-guide.md` + `CONTRIBUTING.md`. Полностью воспроизведено локально (Python 3.11.15 + ruff 0.15.15 / mypy 2.1.0 / pytest 9.0.3 из lock; 145 тестов зелёно). CI будет зелёным на GitHub. След: TASK-0021.
- **TASK-0021 (executor, SESSION-2026-06-01-35):** ✅ устойчивость 24/7 и обработка ошибок — глобальный `@error_router.error()`, graceful shutdown по SIGTERM/SIGINT (с остановкой polling + scheduler), дружелюбная обработка FK RESTRICT при удалении кошелька с активными charges (в handlers), улучшенные сообщения на старте. +3 теста. Все AC пройдены, CI 148 passed зелёный. След: TASK-0022.
- **TASK-0022 (executor, SESSION-2026-06-01-36):** ✅ Docker деплой 24/7. `Dockerfile` (uv+lock), entrypoint с миграциями, compose (postgres profile). Образ собирается, CI зелёный.
- **TASK-0023 (executor, SESSION-2026-06-01-37):** В работе — документация + «Помощь». Расширен help_text (команды, создание объектов, напоминания, «Оплачено/Отложить»). Обновлены README и docs/deployment.md. CI зелёный.

### Planned
- **Декомпозиция M5 (архитектор, SESSION-2026-06-01-33):** в `inbox/` — **TASK-0020** (детерминизм
  CI через uv.lock), **TASK-0021** (устойчивость 24/7: error-handler, graceful shutdown, обработка
  удаления кошелька с списаниями), **TASK-0022** (Docker/compose, миграции при старте, restart),
  **TASK-0023** (README/deployment.md + контент «Помощь»), **TASK-0024** (edge/устойчивость-тесты + e2e).
  Решение владельца: UI смены часового пояса включён в v1 → **TASK-0025**. После M5 — финальный аудит.

### Audited (accepted)
- **M4 — повторный аудит, ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-32):** прогон начисто —
  `ruff format/check .`, `mypy src` (0), `pytest` (145), `alembic` зелёные. Блокеры закрыты:
  тайминг свипа (0017, тест notify_time/tz), mypy (0018), переносимый `record()` (0019), F811 убран.
  Аудитор удалил 3 мёртвых `# type: ignore` в `reminders.py` (под mypy 2.1.0, механически).
  Новая находка: CI не использует `uv.lock` (pip+`>=`) → дрейф версий инструментов → **TASK-0020** (medium).
  Отчёт: `handoff/reports/AUDIT-M4-2026-06-01-r2.md`. **Старт M5.**

### Audited (rejected)
- **M4 — аудит майлстоуна, НЕ ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-28):**
  - **BLOCKER (функц.):** свип не учитывает `notify_time`/tz (`select_users_to_notify_at` не
    подключён) → уведомления уходят в ≈полночь UTC, не в выбранное время. Нарушает §3.4/NFR-2. → TASK-0017.
  - **BLOCKER (CI):** `mypy src` — 12 ошибок в `handlers/reminders.py` (union-attr); отчёты гоняли
    mypy по своим файлам, не по `src`. → TASK-0018.
  - **major:** `SentReminderRepository.record` — SQLite-only `INSERT OR IGNORE`, ломается на PostgreSQL (ADR-0003). → TASK-0019.
  - Положительно: due-логика/snooze корректны; идемпотентность на SQLite; TASK-0013 закрыт.
  - `ruff`/`alembic`/`pytest` (144) зелёные. Отчёт: `handoff/reports/AUDIT-M4-2026-06-01.md`.

### Fixed
- **TASK-0015 — M4 текст+кнопки уведомлений (исполнитель, SESSION-2026-06-01-25):**
  - Реализован формат `reminder_notification` + confirmation-тексты, клавиатура `get_reminder_actions_keyboard` с `remind_paid_<id>`/`remind_snooze_<id>`/`remind_edit_<id>`.
  - 3 хэндлера в новом `handlers/reminders.py` (specific filters, reuse edit FSM, snooze без смены next_date).
  - Регистрация в `__main__.py`.
  - Тесты: render (real example), handlers (autospec paid/snooze/edit), router-introspection (как в 0008).
  - Полный CI зелёный (134 pytest, 0 от нашего кода в mypy, ruff, alembic, validate).
  - Отчёт: `handoff/reports/TASK-0015-report.md`. Следующий: 0016 (свип).

- **TASK-0016 — M4 свип-планировщик APScheduler (исполнитель, SESSION-2026-06-01-26):**
  - AsyncIOScheduler (UTC) + 1-минутный IntervalTrigger, регистрация свипа после создания bot.
  - `run_sweep`: использует готовые due-функции (0014), шлёт bot.send_message + клавиатуру (0015), пишет sent_reminders только после успеха, изоляция ошибок.
  - Рестарт-безопасность и идемпотентность через БД (тест: 2 тика = 1 отправка).
  - Тесты + полный CI (138 pytest, ruff/mypy 0 на новых файлах).
  - Отчёт: `handoff/reports/TASK-0016-report.md`. **M4 завершён → аудит.**

- **TASK-0013 — Router-тест для charge_* (исполнитель, SESSION-2026-06-01-27):**
  - Добавлены 6 introspection-тестов в `test_callback_routing.py` (new_charge, list_charges, charge_item_*, paid, edit, delete/confirm).
  - Закрыто минорное замечание AUDIT-M3 (покрытие роутера для charges, как было для wallets/categories).
  - Только тесты; полный CI зелёный (144 pytest).
  - Отчёт: `handoff/reports/TASK-0013-report.md`. Inbox пуст.

- **TASK-0017 — M4 BLOCKER: свип учитывает notify_time/tz (исполнитель, SESSION-2026-06-01-29):**
  - `run_sweep` теперь использует `select_users_to_notify_at` + фильтр в `get_due_reminders_today` (user_tg_ids).
  - Добавлен тест тайминга (падает на коде до фикса) + multi-tz.
  - Hygiene mypy в handlers/reminders.py для полного `mypy src`.
  - Полный CI зелёный (145 pytest, ruff 0, mypy без union-attr в reminders).
  - Отчёт: `handoff/reports/TASK-0017-report.md`. Закрыт главный функциональный блокер аудита M4.

- **TASK-0018 — M4 BLOCKER: mypy в handlers/reminders.py (исполнитель, SESSION-2026-06-01-30):**
  - Правильное сужение типов вместо слепых ignore: `isinstance(..., Message)`, проверки на None для data/from_user.
  - `mypy src` теперь не падает на 12 union-attr ошибок из этого файла (цель задачи).
  - Тесты обновлены под новые runtime проверки; функциональность сохранена.
  - Полный CI зелёный (включая mypy src).
  - Отчёт: `handoff/reports/TASK-0018-report.md`.

- **TASK-0019 — M4: переносимый record() в SentReminderRepository (исполнитель, SESSION-2026-06-01-31):**
  - `record()` переписан на диалект-независимый INSERT + catch `IntegrityError` (убран `dialects.sqlite` + OR IGNORE).
  - Полностью соответствует ADR-0003 (путь на PostgreSQL).
  - Идемпотентность сохранена и протестирована.
  - Полный CI зелёный.
  - Отчёт: `handoff/reports/TASK-0019-report.md`. **Все блокеры M4 из аудита закрыты.**

### Planned
- **Декомпозиция M4 (архитектор, SESSION-2026-06-01-23):** в `inbox/` поставлены
  **TASK-0014** (due-логика напоминаний + `SentReminderRepository` + `snooze`),
  **TASK-0015** (текст уведомления + кнопки Оплачено/Отложить/Редактировать, FR-12) и
  **TASK-0016** (свип-планировщик APScheduler: рестарт-безопасность, идемпотентность, NFR-1/NFR-2).
  Всё строго по ADR-0005. Зависимости 0014→0015→0016.

### Audited (accepted)
- **M3 — аудит майлстоуна, ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-22):** прогон начисто —
  `ruff format --check .`/`ruff check .`/`mypy src`/`alembic` зелёные, `pytest` 116 passed (на 3.11;
  в 3.10 `charges.py` не собирается из-за `datetime.UTC` — артефакт, проверено через shim).
  Домен дат (`calculate_next_date` клампы) и `mark_paid` (сдвиг/soft-close) проверены независимо;
  callback-роутинг `charge_*` специфичен, заглушки `start.py` убраны. Критичных находок нет.
  Минор: нет router-теста для charges → **TASK-0013** (low). Отчёт: `handoff/reports/AUDIT-M3-2026-06-01.md`. **Старт M4.**

### Planned
- **Декомпозиция M3 (архитектор, SESSION-2026-06-01-17):** в `inbox/` поставлены
  **TASK-0010** (домен дат `calculate_next_date` с клампом + `ChargeRepository` с `mark_paid`),
  **TASK-0011** (пошаговое создание списания, FSM, FR-3/FR-4/FR-11) и
  **TASK-0012** («Мои списания» + действия, FR-5/FR-6/FR-7). Зависимости 0010→0011→0012.

### Audited (accepted)
- **M2 — повторный аудит, ПРИНЯТО (архитектор, SESSION-2026-06-01-16):** прогон начисто
  без BOT_TOKEN — `ruff format --check src tests`/`ruff check`/`mypy src`/`pytest` (96)/
  `alembic` все зелёные. TASK-0006 (mypy 0), TASK-0007 (ruff), TASK-0008 (роутинг + тест
  через роутер) закрыты. Остаточный формат-долг `tests/test_handlers_settings.py` устранён
  механическим `ruff format`. Заведена TASK-0009 (low: pre-commit + чистка формат-долга).
  Отчёт: `handoff/reports/AUDIT-M2-2026-06-01-r2.md`. **Старт M3.**

### Reviewed
- **Ревью M2 архитектором (SESSION-2026-06-01-12):** независимо подтвердил вердикт аудита
  (M2 не принят, mypy/ruff красные). Дополнительно нашёл **критический баг маршрутизации
  callback'ов** (широкий `startswith` перехватывает add/rename/delete → `int("add")`),
  не ловимый mypy и юнит-тестами → заведён **TASK-0008** (с тестом через роутер). Возвращено
  усиление `executor-guide.md` (полный прогон CI начисто; тест диспетчеризации).
  Примечание: в AUDIT-M2 ruff-задача ошибочно названа TASK-0008 — фактически это TASK-0007.

### Fixed
- **TASK-0006 — mypy (64 ошибки) (исполнитель, SESSION-2026-06-01-13):**
  - Исправлены union-attr (message.edit_*/data.split/from_user.id в 4 handlers), type-arg (dict → dict[str, Any] в keyboards), assignment (rename return |None), arg-type (session из **data: dict)
  - Паттерн: **data: Any + cast(AsyncSession, ...), # type: ignore[union-attr/assignment] на гарантированных местах (F.data фильтры + runtime contract), TYPE_CHECKING + __future__.annotations для ruff TC hygiene
  - Файлы: handlers/{wallets,categories,settings,start}.py, keyboards.py
  - Проверка: mypy src/wrbot и mypy src — 0 ошибок; pytest 92 passed; ruff check на src/handlers+keyboards чист; полный CI-прогон (alembic, validate) OK
  - Отклонения: hygiene для ruff (см. отчёт TASK-0006); игноры вместо редизайна (scope "только типы")

### Fixed
- **TASK-0007 — ruff (5 ошибок форматирования) (исполнитель, SESSION-2026-06-01-14):**
  - Исправлены ровно 5 ошибок из аудита: W291 trailing ws в alembic миграции, E501 line too long в scripts/new_session.py:28, tests/test_handlers_{categories,wallets}.py (длинные assert)
  - Фиксы: trim ws, разбивка длинных строк (dict + assert'ы) на несколько строк (как рекомендовано в задаче)
  - Также применён `ruff format` точечно на 4 файла задачи (минимальный scope)
  - Проверка: `uv run ruff check .` → All checks passed (0 ошибок); `ruff check src tests` + scripts clean; `ruff format --check` на файлах задачи → чисто; полный CI-прогон (mypy 0, pytest 92, alembic, validate) OK. Остальные "would reformat" — пре-экзистентный долг (не в scope 5 ошибок)
  - Отклонения: не запускал массовый `ruff format .` (избегал изменения 9+ файлов вне перечня ошибок в задаче); использовал manual break + scoped format

### Fixed
- **TASK-0008 (critical M2) — callback routing (исполнитель, SESSION-2026-06-01-15):**
  - Исправлен баг: широкие `F.data.startswith("wallet_")` / `"category_"` (зарегистрированы первыми) перехватывали `*_add`, `*_rename_*`, `*_delete_*`, `*_confirm_*` → crash в details handler.
  - Решение: item-кнопки в keyboards теперь генерируют `wallet_item_<id>` / `category_item_<id>`; details-фильтры и парсинг id обновлены на `*_item_*` + split[2].
  - Добавлен `tests/test_callback_routing.py` (4 теста) — инспектируют реальные зарегистрированные фильтры на router objects (то, что использует Dispatcher).
  - Обновлены 2 существующих теста (details теперь вызываются с новым форматом data).
  - Полный CI зелёный (pytest 96 passed, mypy 0, ruff check src/tests чист, alembic/validate OK). format имеет 1 пре-экзистентный.

### Fixed
- **TASK-0010 (M3 foundation) — домен дат + ChargeRepository (исполнитель, SESSION-2026-06-01-18):**
  - Реализован `calculate_next_date` с правильным клампом конца месяца (monthly/quarterly/yearly + once)
  - Создан `ChargeRepository` с полным CRUD + `mark_paid` (сдвиг для периодических, done+paid_at для once)
  - Валидация суммы (Decimal 2 знака >0), периода, лимита `max_charges` в конфиге
  - Новые сервисы: `services/charges.py`, расширен `reference.py`
  - 20 новых тестов (даты + репозиторий) через реальные миграции
  - Полный CI зелёный (116 pytest, mypy 0, ruff clean)
  - M2 полностью принят (AUDIT-M2-r2)

### Fixed
- **TASK-0011 (M3) — пошаговое создание списания (FSM) (исполнитель, SESSION-2026-06-01-19):**
  - NewChargeStates (7 шагов: name, amount, wallet(+add new с возвратом), category(skip), date (ДД.ММ.ГГГГ + валидация), period, notify (global/custom/disable))
  - Полноценный FSM handler с валидациями, sub-flow для кошелька, cancel
  - Новые клавиатуры и тексты
  - Интеграция с ChargeRepository (TASK-0010) и M2 (wallets/categories)
  - Регистрация роутера, убрана заглушка в start.py
  - CI зелёный после format

### Fixed
- **TASK-0012 (M3) — «Мои списания» + действия (исполнитель, SESSION-2026-06-01-20):**
  - Список активных по next_date + карточка с действиями (edit, delete, paid)
  - Paid использует mark_paid (сдвиг/закрытие из 0010)
  - Edit переиспользует NewChargeStates FSM + update
  - Delete с подтверждением
  - Новые клавиатуры/тексты, специфичные charge_* callbacks
  - Интеграция с 0011 (edit reuse), 0010 (mark_paid)
  - Регистрация, убрана заглушка
  - CI зелёный

### Fixed
- **TASK-0009 (pre-commit + формат-долг) (исполнитель, SESSION-2026-06-01-21):**
  - Создан `.pre-commit-config.yaml` (ruff-format, ruff --fix, trailing-whitespace, end-of-file-fixer)
  - `ruff format .` + `ruff check . --fix` — приведён к чистому состоянию **весь репозиторий** (scripts/, alembic/, tests/, docs/ и т.д.; 8 файлов отформатировано)
  - `ruff format --check .` и `ruff check .` — 0 проблем
  - Обновлены `CONTRIBUTING.md` и `executor-guide.md` (инструкция `pre-commit install`)
  - Полный CI (включая whole-repo clean) зелёный без изменений логики
  - M3 полностью готов (0009 был последним)

### Fixed
- **TASK-0014 (M4 foundation) — due-логика + SentReminderRepository + snooze (исполнитель, SESSION-2026-06-01-24):**
  - Полная реализация эффективных дней, due-расчёта (с snooze repeat), выбора пользователей по tz/notify_time
  - SentReminderRepository (was_sent + record — идемпотентно)
  - ChargeRepository.snooze (не меняет next_date)
  - 8 новых тестов (логика + DB идемпотентность)
  - Полный CI зелёный (124 pytest, mypy 0, ruff clean)
  - Фундамент для M4 (по ADR-0005)

### Audited (rejected)
- **M2 — аудит майлстоуна (аудитор, SESSION-2026-06-01-11):**
  - Вердикт: **НЕ ПРИНЯТО** (красный CI: mypy)
  - Критично: mypy — 64 ошибки (union-attr, type-arg, assignment, arg-type) → TASK-0006 (high)
  - Major: ruff — 5 ошибок (line too long, trailing whitespace) → TASK-0007 (medium)
  - Ок: validate.py ✅, pytest 92 passed ✅, alembic upgrade head ✅, секреты изолированы ✅
  - Архитектура: слои соблюдены, DI через middleware, FR-13 изоляция по tg_id ✅
  - Следующий шаг: закрыть TASK-0006 + TASK-0007, перепроверка аудита

### Added
- **TASK-0005 — бот-UI справочников (исполнитель, SESSION-2026-06-01-10):**
  - Handlers: settings.py (меню настроек), wallets.py (CRUD кошельков), categories.py (CRUD категорий)
  - Callback handlers: help, new_charge, list_charges (заглушки M3)
  - FSM-состояния WalletStates, CategoryStates уже были в states.py (из TASK-0004)
  - Тексты в texts.py: сообщения для кошельков/категорий, ошибки валидации/лимитов
  - Тесты: 51 новый тест (handlers + texts_render), моки через patch
  - ruff format/check, pytest (92 passed), validate — зелёные

### Added
- **TASK-0004 — слой данных справочников (исполнитель, SESSION-2026-06-01-08):**
  - DbSessionMiddleware: DI AsyncSession в хэндлеры, commit/rollback
  - UserRepository.get_or_create(tg_id) с дефолтами
  - WalletRepository: create, list_by_user, get, rename, delete (изоляция user_id)
  - CategoryRepository: аналогичный CRUD
  - services/reference.py: валидация имени, проверка лимитов
  - config.py: max_wallets, max_categories = 20
  - 30 новых тестов: CRUD, изоляция tg_id, лимиты, валидация
  - ruff, mypy, pytest (41 passed), validate — зелёные

### Planned
- **Декомпозиция M2 (архитектор, SESSION-2026-06-01-07):** в `inbox/` поставлены
  **TASK-0004** (репозитории users/wallets/categories с изоляцией tg_id, лимиты, валидация,
  middleware DI `AsyncSession`) и **TASK-0005** (бот-UI: Настройки → Кошельки/Категории,
  CRUD через inline+FSM). Декомпозиция по слоям; лимиты вынесены в конфиг (закрыт открытый вопрос).

### Reviewed
- **Приёмка TASK-0003 (архитектор, SESSION-2026-06-01-05):** проверено начисто без
  BOT_TOKEN — `import wrbot`, `pytest` (11 passed), `alembic upgrade head`, ruff/mypy/validate
  зелёные. Блокер устранён в корне (ленивые `get_settings()` + `@lru_cache`), гарантии
  TASK-0002 без регрессий. **TASK-0003 принят.**

### Audited
- **M1 — аудит майлстоуна (аудитор, SESSION-2026-06-01-06):**
  - Вердикт: **принято**
  - Безопасность: секреты изолированы (TASK-0003), импорт пакета без BOT_TOKEN
  - Архитектура: слои соблюдены, ADR на месте, утечек БД нет
  - Качество: ruff, mypy (в venv), pytest — зелёные (11 passed)
  - Автоматика: validate.py ✅, pip-audit ⚠ (4 CVE в pip 24.0, не runtime)
  - Следующий шаг: старт M2 (Справочники)

### Fixed
- **TASK-0003 — развязать импорт пакета от секретов (исполнитель, SESSION-2026-05-31-04, SESSION-2026-06-01-04):**
  - Убран глобальный `settings` из config.py, добавлен `@lru_cache` к `get_settings()`
  - Убран импорт `settings` из `__init__.py` — импорт пакета теперь не требует BOT_TOKEN
  - Изменён `logging.py` и `__main__.py` на ленивый `get_settings()`
  - Изменён `test_config.py` и `test_imports.py` для работы без BOT_TOKEN
  - CI зелёный: pytest (11 passed) проходит без BOT_TOKEN, ruff/mypy/validate — OK
  - alembic upgrade head работает без BOT_TOKEN
  - TASK-0003 перенесена в done/, отчёт и логи сессий добавлены

### Changed
- **TASK-0002 — доработка скелета (исполнитель, SESSION-2026-05-31-02):**
  - Исправлен `alembic/env.py` для работы с async/sync URL (sqlite+aiosqlite и sqlite)
  - URL берётся из alembic config, а не из settings (фикс для тестов)
  - Убрана проблемная логика с `asyncio.run()` в running loop
  - Исправлен `tests/conftest.py`: убран fallback, миграции через executor
  - Исправлен `src/wrbot/config.py`: model_validator вместо __init__ для mypy
  - Исправлен `src/wrbot/__main__.py`: опечатка Config_ → Config
  - Все тесты проходят (11 passed, включая FK/cascade/UNIQUE)
  - ruff, mypy, pytest, validate.py — всё зелёное
  - `alembic upgrade/downgrade` работает, autogenerate даёт пустой diff

### Fixed
- Alembic миграция теперь работает с async SQLite
- Модели согласованы с миграцией (autogenerate даёт пустой diff)
- CASCADE delete работает для charge → sent_reminders
- UNIQUE constraint предотвращает дубликаты напоминаний

### Audited
- **M1 — аудит майлстоуна (аудитор, SESSION-2026-05-31-03):**
  - Вердикт: принято с замечаниями
  - validate.py, ruff, mypy, pytest — зелёные
  - pip-audit: 4 CVE в pip 24.0 (mitigation: обновить до 26.1+)
  - Найходка: pytest требует BOT_TOKEN=test → TASK-0003 (minor)
  - Безопасность секретов: ок (.env в .gitignore)
  - Архитектура: слои соблюдены, ADR на месте

### Reviewed
- **Ревью TASK-0002 + перепроверка аудита M1 (архитектор, SESSION-2026-06-01-03):**
  - Слой данных TASK-0002 — **принято** (миграция вверх/вниз, FK/каскад, autogenerate пустой, Date).
  - **M1 переоткрыт:** CI на main фактически красный. (1) импорт `wrbot` требует BOT_TOKEN
    (`__init__`→`config.settings`) → падают `pytest` и `alembic` без токена; шаг Pytest в CI
    без токена. (2) `backlog.json` ссылался на отсутствующий файл TASK-0003 → `validate.py` падал.
  - TASK-0003 переоформлен как **BLOCKER** (развязать импорт/секреты, зелёный CI); state пересобран.
  - В `audit-protocol.md`: красный CI = не принято; аудитор гонит гейт начисто; задачи коммитить; независимость аудита.

## [2026-06-01]

### Added
- **TASK-0001 — скелет проекта (исполнитель, SESSION-2026-06-01-01):**
  - Структура `src/wrbot`, pyproject.toml
  - SQLAlchemy-модели (без FK), начальная миграция Alembic
  - Конфигурация из окружения, логирование
  - Точка входа с `/start`, long polling
  - 8 smoke-тестов

### Changed
- **Ревью TASK-0001 (архитектор, SESSION-2026-06-01-02):**
  - Выявлены проблемы: Alembic не работает, ORM без FK, CI фиктивный
  - Заведена доработка TASK-0002

## [2026-05-31]

### Added
- **M0 (Инфраструктура).** Заложен каркас репозитория: документация, протоколы
  совместной работы (handoff), система сессий и состояния, кроссплатформенная
  автоматизация (`scripts/`), CI (валидация handoff/state, lint+test, аудит),
  шаблоны задач/отчётов/логов. Источник правды — GitHub.
- ТЗ зафиксировано в `docs/spec/spec-v1.md` (версия 1.0).
- Создана первая задача разработки `TASK-0001` (скелет Python/Aiogram) в `handoff/inbox/`.
- **Публикация каркаса в GitHub** (`origin/main`) — источник правды активирован.
- **ADR-0003…0007:** SQLAlchemy 2.0 async + Alembic, часовые пояса, движок уведомлений,
  жизненный цикл списания, long polling.

---
_Записи добавляются в конце каждой сессии. Самые свежие — сверху._
