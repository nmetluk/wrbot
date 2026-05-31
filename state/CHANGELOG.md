# Project Session Changelog

Журнал сессий и изменений проекта wrbot. Даты в UTC.

**Назначение:** Этот файл — машиночитаемый журнал сессий, каждый шаг разработки.
Для пользователей см. `/CHANGELOG.md` (история версий).

## [Unreleased]

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
