---
id: TASK-0022
title: "M5: развёртывание 24/7 (Docker, compose, миграции при старте)"
milestone: M5
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T23:00:00Z
depends_on: [TASK-0021]
---

# TASK-0022: Развёртывание 24/7

## Цель
Дать воспроизводимый способ запустить бота 24/7 (NFR-1): контейнеризация, авто-миграции,
перезапуск при сбое.

## Контекст
- ТЗ §5 (24/7). Стек: Python 3.11, long polling (ADR-0007), SQLite старт / PostgreSQL (ADR-0003).
- Сейчас нет `Dockerfile`/`docker-compose`/`docs/deployment.md`.

## Критерии приёмки (проверяемые)
- [ ] **Dockerfile** (Python 3.11-slim, установка через `uv`/lock для воспроизводимости),
      непривилегированный пользователь, запуск `python -m wrbot`.
- [ ] **Entrypoint** применяет `alembic upgrade head` перед стартом бота (идемпотентно).
- [ ] **docker-compose.yml**: сервис бота с `restart: unless-stopped`, env из `.env`,
      volume для SQLite-данных (`data/`); опциональный профиль `postgres` (сервис Б

      с `DATABASE_URL` на asyncpg) — задел на ADR-0003.
- [ ] **.dockerignore** (без `.git`, `.venv`, кэшей, `.env`). `.env.example` актуален.
- [ ] Healthcheck или хотя бы документированный способ проверить, что бот жив.
- [ ] Сборка образа и `docker compose config` валидны (проверить локально, привести вывод в отчёте).
- [ ] Весь CI начисто зелёный.

## Ожидаемые артефакты
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`, entrypoint-скрипт (кроссплатформенно/документировано).

## Ограничения / заметки
- Секреты только через env/`.env` (не в образ). Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0021
