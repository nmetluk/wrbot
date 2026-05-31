---
id: TASK-0002
title: Доработка скелета: рабочая Alembic-миграция, FK в моделях, реальный CI
milestone: M1
status: inbox
created_by: architect
created_at: 2026-05-31T21:58:55Z
depends_on: [TASK-0001]
---

# TASK-0002: Доработка скелета (рабочая миграция, FK, реальный CI)

## Цель
TASK-0001 заложил структуру, но ключевой результат ADR-0003 — миграции Alembic —
не работает, ORM-модели расходятся со схемой миграции, а CI фиктивный (`|| true`).
Привести слой данных и процессную проверку в рабочее, согласованное состояние.

## Контекст
- Ревью TASK-0001: SESSION-2026-06-01-02 (архитектор). Поверхность скелета принята
  (структура, хэндлеры, ruff/mypy/pytest зелёные), но слой данных и CI требуют доработки.
- Связанные ADR: **ADR-0003** (SQLAlchemy+Alembic), **ADR-0004** (tz/UTC),
  **ADR-0005** (`sent_reminders`), **ADR-0006** (Decimal, status), **ADR-0007** (long polling).
- Правила: `CLAUDE.md` — «миграции только через Alembic, никаких `CREATE TABLE` в коде»,
  «FK и индексы обязательны», «ON DELETE CASCADE где уместно», anti-drift (мокать со spec,
  тесты должны ловить рассинхрон).
- Файлы: `alembic/env.py`, `src/wrbot/db/models.py`, `src/wrbot/__main__.py`,
  `tests/conftest.py`, `.github/workflows/ci.yml`, `src/wrbot/config.py`.

## Найдено в ревью (что чинить)
1. **`alembic upgrade head` не работает:** `alembic/env.py` импортирует `wrbot` (пакет не
   на путях) и не сконфигурирован под async-движок (`sqlite+aiosqlite`) → `MissingGreenlet`.
2. **ORM-модели ≠ миграция:** в `db/models.py` связи заданы голым `Integer` без `ForeignKey`/
   `relationship`/cascade, тогда как миграция содержит FK и `ON DELETE CASCADE`. `autogenerate`
   будет «дрейфовать». 
3. **Обход Alembic через `create_all`:** в `__main__.py` и `tests/conftest.py` схема строится
   `Base.metadata.create_all` — это (а) нарушает правило «только Alembic», (б) создаёт схему
   БЕЗ FK (из моделей), отличную от миграции. Тест проверяет только `Base.metadata.tables`,
   миграция не покрыта — классический «слабый тест маскирует рассинхрон».
4. **CI фиктивный:** в `ci.yml` каждый шаг с `|| true` → CI не может упасть; `alembic upgrade
   head` и `validate.py` не запускаются.
5. **Сироты:** каталоги верхнего уровня `repositories/` и `services/` (дубли `src/wrbot/...`)
   и лишний корневой `CHANGELOG.md` (канон — `state/CHANGELOG.md`).
6. **config:** `bot_token` по умолчанию `"test_token"` (в проде должно падать при отсутствии,
   а тесты — выставлять env); `database_url` по умолчанию содержит `~`, который не раскроется.
7. **Типы дат:** `next_date`, `target_date`, `snoozed_until` — `DateTime`, а по `data-model.md`
   это `DATE`.

## Критерии приёмки (проверяемые)
- [ ] `alembic upgrade head` **успешно поднимает схему на свежей SQLite** из чистого состояния
      (без правки PYTHONPATH вручную — пакет ставится `pip install -e .`, либо `env.py` чинит путь),
      и корректно работает с async-URL (`sqlite+aiosqlite`). `alembic downgrade base` тоже проходит.
- [ ] **ORM-модели в `db/models.py` соответствуют миграции:** реальные `ForeignKey`
      (users.tg_id, wallets.id, categories.id, charges.id), `ON DELETE CASCADE` для
      `sent_reminders.charge_id`, индексы. `alembic revision --autogenerate` на актуальной БД
      даёт **пустой** diff (модели и миграция согласованы).
- [ ] **Схема строится только через Alembic.** Убрать `Base.metadata.create_all` из
      `__main__.py` (использовать `alembic upgrade head` при старте/деплое). В тестах схему
      поднимать **через миграцию** (`alembic upgrade head` на временной БД), а не `create_all`.
- [ ] Тест на FK/каскад: удаление `charge` каскадно удаляет связанные `sent_reminders`
      (с включённым `PRAGMA foreign_keys=ON` для SQLite); тест на `UNIQUE(charge_id,target_date,days_before)`.
- [ ] **CI — реальный гейт:** убрать все `|| true`; шаги `ruff check`, `ruff format --check`,
      `mypy src`, `pytest`, `alembic upgrade head`, `python scripts/validate.py` падают при ошибке.
      Пакет ставится так, чтобы импорт `wrbot` работал в CI.
- [ ] Удалить сироты `repositories/` и `services/` в корне. По `CHANGELOG`: оставить один
      источник — либо корневой `CHANGELOG.md` (тогда обновить ссылки и убрать дубль из `state/`),
      либо `state/CHANGELOG.md`; **зафиксировать выбор** (мелкий ADR или строка в README). Рекомендация: корневой `CHANGELOG.md` для релизов, `state/CHANGELOG.md` — журнал сессий; явно развести назначение в обоих файлах.
- [ ] `config.py`: `bot_token` обязателен (без рабочего дефолта; в проде падает при отсутствии,
      тесты подставляют env/fixture); `database_url` по умолчанию без `~` (или с `Path.expanduser`).
- [ ] `next_date`/`target_date`/`snoozed_until` → тип `Date` (и в моделях, и в миграции),
      согласовать с `data-model.md`.
- [ ] CI зелёный честно (lint, типы, тесты, миграция, валидация handoff/state).

## Ожидаемые артефакты
- Код: `src/wrbot/db/models.py`, `src/wrbot/__main__.py`, `src/wrbot/config.py`, `alembic/env.py`.
- Тесты: `tests/conftest.py` (миграция вместо create_all), новые тесты FK/каскад/UNIQUE.
- CI: `.github/workflows/ci.yml` (без `|| true`, со step'ами alembic + validate).
- Чистка: удалить `repositories/`, `services/` в корне; решить судьбу `CHANGELOG.md`.

## Ограничения / заметки
- Не реализуй бизнес-логику (CRUD/уведомления) — это M2–M4. Только корректность фундамента.
- Кроссплатформенно (pathlib, LF), секреты в `.env`. Перед `done` — отчёт, лог сессии
  (уникальный ID, см. ниже), обновление state, push.
- **ID лога сессии — уникальный.** Если на дату уже есть `SESSION-YYYY-MM-DD-NN`, увеличь `NN`,
  не перезаписывай чужой лог (в TASK-0001 архитекторский лог был затёрт).

## Зависимости
Зависит от: TASK-0001
