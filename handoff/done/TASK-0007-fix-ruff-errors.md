---
id: TASK-0007
title: Исправить ruff ошибки форматирования
milestone: M2
status: inbox
priority: medium
created_by: architect
created_at: 2026-06-01T04:47:15Z
depends_on: [TASK-0005]
---

# TASK-0007: Исправить ruff ошибки форматирования

## Цель
Исправить 5 ошибок ruff (line too long, trailing whitespace) для прохождения CI.

## Контекст
- Аудит SESSION-2026-06-01-11: ruff находит 5 ошибок (было 15, частично исправлено `--fix`)
- Большинство исправимы автоматически, часть требует ручного редактирования

## Ошибки
1. **alembic/versions/20260531_2205_bf12de07eec5_*.py**:
   - Строка 4: trailing whitespace в `Revises: `
   - Строка 76: line too long (103 > 100)

2. **scripts/new_session.py**:
   - Строка 28: line too long (101 > 100)

3. **tests/test_handlers_categories.py**:
   - Строка 335: line too long (125 > 100)

4. **tests/test_handlers_wallets.py**:
   - Строка 336: line too long (125 > 100)

## Критерии приёмки
- [ ] `uv run ruff check .` проходит без ошибок
- [ ] `uv run ruff format --check` проходит без ошибок
- [ ] CI зелёный

## Ожидаемые артефакты
- Код: исправления в `alembic/versions/*.py`, `scripts/*.py`, `tests/*.py`

## Ограничения / заметки
- Для миграций alembic можно сузить проверку (pyproject.toml per-file-ignores), но лучше исправить
- Длинные assert в тестах можно разбить на строки

## Зависимости
Зависит от: TASK-0005 (UI справочников)
