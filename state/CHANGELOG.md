# Project Session Changelog

Журнал сессий и изменений проекта wrbot. Даты в UTC.

**Назначение:** Этот файл — машиночитаемый журнал сессий, каждый шаг разработки.
Для пользователей см. `/CHANGELOG.md` (история версий).

## [Unreleased]

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
