---
id: TASK-0009
title: Pre-commit hooks и устранение формат-долга (анти-дрейф)
milestone: M2
status: inbox
priority: low
created_by: architect
created_at: 2026-06-01T16:00:00Z
depends_on: [TASK-0008]
---

# TASK-0009: Pre-commit hooks + чистка формат-долга

## Цель
Прекратить повторяющийся дрейф форматирования (CI-шаг `ruff format --check` падал в
TASK-0005/0007/0008 из-за неотформатированных файлов). Завести pre-commit hooks и
привести весь репозиторий к чистому `ruff format`.

## Контекст
- Несколько раз CI был красным/требовал доработки только из-за `ruff format`.
- В соседнем проекте `whois-watcher` это решено через `.pre-commit-config.yaml`.
- Найдено в AUDIT-M2-r2 (SESSION-2026-06-01-16).

## Критерии приёмки (проверяемые)
- [ ] `.pre-commit-config.yaml`: хуки `ruff format`, `ruff check --fix`, и (опц.)
      end-of-file/trailing-whitespace. Зафиксирована версия ruff.
- [ ] `ruff format --check .` — чисто по ВСЕМУ репозиторию (включая `scripts/`, `alembic/`, `tests/`).
- [ ] `ruff check .` — чисто.
- [ ] Инструкция в `CONTRIBUTING.md`/`executor-guide.md`: `pre-commit install` после клонирования.
- [ ] Весь CI начисто без BOT_TOKEN зелёный (ruff format/check, mypy, pytest, alembic, validate).
- [ ] Никаких изменений логики (только формат + конфиг хуков).

## Ожидаемые артефакты
- `.pre-commit-config.yaml`, правки `CONTRIBUTING.md`/`docs/workflow/executor-guide.md`,
  отформатированные файлы.

## Ограничения / заметки
- Чистый формат-проход; бизнес-логику и тесты по сути не менять.
- Низкий приоритет — не блокирует старт M3, но желательно закрыть до накопления нового долга.

## Зависимости
Зависит от: TASK-0008
