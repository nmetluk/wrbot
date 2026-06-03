---
id: TASK-0038
title: "M6 BLOCKER: нестабильный тест бэкапа (зависимость от порядка через get_settings lru_cache)"
milestone: M6
status: inbox
priority: high
created_by: architect
created_at: 2026-06-03T08:00:00Z
depends_on: [TASK-0033]
---

# TASK-0038: Детерминировать тест бэкапа и настройки в тестах

## Цель
Сделать гейт воспроизводимо зелёным: `test_backup.py::test_sqlite_backup_creates_valid_file`
падает в полном прогоне (проходит в одиночку) из-за кэша `get_settings`.

## Корневая причина (подтверждено аудитом M6, AUDIT-M6-2026-06-03)
`services/backup.py:create_backup()` берёт `get_settings().database_url` (под `@lru_cache`).
Тест патчит только `BACKUPS_DIR`, не сбрасывает кэш и не задаёт БД. В полном прогоне
`get_settings()` уже закэширован чужим `DATABASE_URL` от предыдущего теста → бэкап
несуществующей/неправильной БД → `success=False` → assert. Зависимость от порядка → flaky CI.

## Критерии приёмки (проверяемые)
- [ ] `pytest` зелёный **детерминированно**, независимо от порядка: проверить
      `uv run pytest` (полный), `pytest tests/test_backup.py` (изолированно) и, для надёжности,
      случайный порядок (`pytest -p randomly` если доступен, или ручная перестановка) — везде зелено.
- [ ] Тест бэкапа герметичен: либо сбрасывает `get_settings.cache_clear()` и monkeypatch
      `DATABASE_URL` на временную БД, либо (предпочтительно) `create_backup(db_url: str | None = None)`
      принимает явный URL (по умолчанию `get_settings().database_url`) — тест передаёт временную БД.
- [ ] (Рекомендуется) autouse-фикстура в `conftest.py`, сбрасывающая кэш `get_settings` между тестами,
      чтобы исключить класс «протёкших настроек» на будущее.
- [ ] Поведение в проде не меняется (по умолчанию берётся `get_settings().database_url`).
- [ ] Весь CI начисто зелёный (`uv run` ruff format/check, mypy, pytest, alembic, validate).

## Ожидаемые артефакты
- Код: `services/backup.py` (опц. параметр `db_url`), `tests/test_backup.py`, `tests/conftest.py` (фикстура).

## Ограничения / заметки
- Только тестовая герметичность/тестопригодность, без изменения логики бэкапа. Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0033
