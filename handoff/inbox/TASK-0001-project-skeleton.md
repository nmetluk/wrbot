---
id: TASK-0001
title: Скелет Python/Aiogram-проекта
milestone: M1
status: inbox
created_by: architect
created_at: 2026-05-31T20:50:08Z
depends_on: []
---

# TASK-0001: Скелет Python/Aiogram-проекта

## Цель
Заложить запускаемый каркас бота: структура пакета `src/wrbot`, управление
зависимостями, конфигурация из окружения, логирование, инициализация БД (схема) и
точка входа, при которой бот поднимается и отвечает на `/start` заглушкой главного
меню. Это фундамент для M2–M4.

## Контекст
- ТЗ: §4 (стек), §3.1 (главное меню), §1.3 (изоляция по `tg_id`).
- Требования: FR-1 (главное меню), FR-14 (русский), NFR-3 (чистый код), NFR-5 (стек), NFR-6 (секреты в окружении), NFR-7 (кроссплатформенность).
- Решения: **ADR-0002** (стек), **ADR-0003** (SQLAlchemy 2.0 async + Alembic),
  **ADR-0004** (поле `tz`, дефолт Europe/Moscow), **ADR-0005** (таблица `sent_reminders`,
  поле `snoozed_until`), **ADR-0006** (`status`/`paid_at`, сумма Decimal), **ADR-0007** (long polling).
- Ориентир по структуре: `docs/architecture/components.md`; **актуальная схема —
  `docs/architecture/data-model.md`** (содержит все поля и таблицы по ADR-0003…0006).

## Критерии приёмки (проверяемые)
- [ ] `pyproject.toml` с зависимостями: aiogram 3.x, APScheduler, **SQLAlchemy 2.0
      (async), Alembic, asyncpg (PostgreSQL), aiosqlite (SQLite)** (ADR-0003), dev-инструменты
      (ruff, mypy, pytest, pytest-asyncio); метаданные; целевая версия Python зафиксирована (3.11+).
- [ ] Структура пакета `src/wrbot/` по `components.md` (config, logging, bot/handlers,
      keyboards, states, texts; services; repositories; db; scheduler; models) — с осмысленными заглушками и docstring.
- [ ] `config.py` читает настройки из окружения/`.env` (BOT_TOKEN, DATABASE_URL,
      DEFAULT_TIMEZONE=Europe/Moscow, LOG_LEVEL). Секрет не хардкодится. `.env.example` актуален.
- [ ] Логирование настроено (уровень из конфига), пишет в `logs/` (gitignored).
- [ ] **Модели SQLAlchemy и начальная миграция Alembic** покрывают полную схему из
      `data-model.md`: `users` (с `tz`, `global_days`, `notify_time`), `wallets`, `categories`,
      `charges` (с `amount` Decimal, `status`, `paid_at`, `snoozed_until`, `individual_days`),
      `sent_reminders` (UNIQUE `charge_id,target_date,days_before`). `alembic upgrade head`
      поднимает схему на SQLite; типы совместимы с PostgreSQL (JSON↔JSONB, NUMERIC). Без `CREATE TABLE` в коде.
- [ ] Точка входа (`python -m wrbot`) поднимает бота (long polling, ADR-0007); `/start` отвечает
      инлайн-меню (➕ Новое списание, 📋 Мои списания, ⚙️ Настройки, ❔ Помощь) — пока заглушки.
      Команды `/help`, `/cancel` зарегистрированы.
- [ ] Тесты `pytest`: хотя бы smoke (импорт пакета, конфиг из окружения, `alembic upgrade head`
      на временной SQLite-БД создаёт все таблицы из `data-model.md`).
- [ ] CI зелёный: `ruff check`, `ruff format --check`, `mypy src`, `pytest`, `python scripts/validate.py`.
- [ ] Документация обновлена: `README` по локальному запуску (как поднять бота), при
      необходимости уточнён `components.md`. Реальный токен в репозиторий не попадает.

## Ожидаемые артефакты
- Код: `src/wrbot/...`, точка входа `src/wrbot/__main__.py`.
- Конфиг сборки: `pyproject.toml` (+ настройки ruff/mypy/pytest).
- Тесты: `tests/...`.
- Документация: раздел «Запуск локально» в `README.md` или `docs/`.

## Ограничения / заметки
- Не реализуй бизнес-логику списаний/уведомлений — только каркас и заглушки (это M2–M4).
- Кроссплатформенно: пути через `pathlib`, без bash-специфики, переносы LF.
- Секреты только в `.env`. Перед `done` — отчёт, обновление state, лог сессии, push.
- Ключевые архитектурные вопросы уже закрыты ADR-0003…0007 — следуй им, не переизобретай.
  Если встретишь НОВЫЙ неоднозначный вопрос (см. «Открытые вопросы» в `docs/requirements.md`) —
  оформи ADR или переведи задачу в `blocked/` с конкретным вопросом, не угадывай.

## Зависимости
Зависит от: нет
