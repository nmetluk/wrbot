---
id: TASK-0020
title: Детерминированный CI — honoring uv.lock (фикс дрейфа версий инструментов)
milestone: M5
status: inbox
priority: medium
created_by: architect
created_at: 2026-06-01T22:40:00Z
depends_on: [TASK-0016]
---

# TASK-0020: Детерминированный CI (версии инструментов из lock)

## Цель
Устранить нондетерминизм гейта: сейчас `uv.lock` фиксирует `mypy==2.1.0`/`ruff==0.15.15`,
но CI ставит `pip install -e ".[dev]"` (с `>=`), резолвя версии заново. Из-за этого
«зелено у исполнителя — красно на CI/у аудитора» (дважды: TASK-0005, TASK-0015/0018).

## Контекст
- Найдено в AUDIT-M4-r2 (SESSION-2026-06-01-32).
- В репо уже есть `uv.lock` (pinned), но `ci.yml` его не использует.

## Критерии приёмки (проверяемые)
- [ ] CI (`.github/workflows/ci.yml`) ставит зависимости **из lock**: `uv sync --frozen`
      (или эквивалент), команды гейта запускаются в этом окружении (`uv run ruff/mypy/pytest/alembic`).
      Никаких `pip install -e ".[dev]"` с открытыми `>=` для dev-инструментов в гейте.
- [ ] Локальный прогон и CI используют **одни и те же** версии ruff/mypy (из `uv.lock`).
- [ ] `executor-guide.md`/`CONTRIBUTING.md`: явно — прогонять гейт через `uv run` (как в CI).
- [ ] (Опц.) Зафиксировать в pyproject совместимые верхние границы или полагаться на lock.
- [ ] Весь CI начисто зелёный на зафиксированных версиях (ruff format/check, mypy, pytest, alembic, validate).

## Ожидаемые артефакты
- `.github/workflows/ci.yml`, при необходимости `docs/workflow/executor-guide.md`, `CONTRIBUTING.md`.

## Ограничения / заметки
- Не менять логику приложения. Цель — воспроизводимость гейта.
- Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0016
