---
id: TASK-0029
title: "Deploy-readiness: унифицировать регистр env-переменных (.env.example vs compose/docs)"
milestone: M5
status: inbox
priority: high
created_by: architect
created_at: 2026-06-02T22:10:00Z
depends_on: [TASK-0022]
---

# TASK-0029: Унификация имён переменных окружения для деплоя

## Цель
Устранить несогласованность регистра env-переменных, которая ломает/делает неоднозначным
деплой на PostgreSQL и путает при развёртывании на удалённом сервере.

## Контекст / приоритет
- **Severity: high (deploy-readiness).** Найдено при проверке готовности к удалённому деплою
  (SESSION-2026-06-02-05).
- `.env.example` использует **нижний** регистр (`bot_token`, `database_url`, `default_timezone`,
  `log_level`), а `docker-compose.yml` (`${DATABASE_URL:-...}`, блок `environment:`),
  `docker/entrypoint.sh` и `docs/deployment.md` — **ВЕРХНИЙ** (`DATABASE_URL`, `BOT_TOKEN`).
- Для дефолтного SQLite совпадает по значению и работает. Но интерполяция compose `${DATABASE_URL}`
  **регистрозависима**: при Postgres-пути пользователь по `.env.example` пишет `database_url=...`
  (нижний) → `${DATABASE_URL}` его не видит → в контейнер попадают и `database_url` (env_file),
  и `DATABASE_URL=<sqlite-дефолт>` (environment override) → неоднозначность/неверная БД.

## Критерии приёмки (проверяемые)
- [ ] Единый регистр во всех артефактах — **UPPERCASE** (конвенция для env): `BOT_TOKEN`,
      `DATABASE_URL`, `DEFAULT_TIMEZONE`, `LOG_LEVEL`. Привести `.env.example`, `docker-compose.yml`,
      `docker/entrypoint.sh`, `docs/deployment.md`, `README` к одному виду.
- [ ] Убрать двусмысленность в compose: либо полагаться только на `env_file: .env` (без дублирующего
      `environment: DATABASE_URL=...`), либо сделать override согласованным. В контейнер не должны
      попадать одновременно `database_url` и `DATABASE_URL` с разными значениями.
- [ ] **Проверка SQLite-пути:** `docker compose up -d --build` со свежим `.env` (только `BOT_TOKEN`)
      → миграции применяются, бот стартует, данные в `./data` персистятся между рестартами.
- [ ] **Проверка Postgres-пути:** `--profile postgres` с `DATABASE_URL=postgresql+asyncpg://...`
      → бот использует именно Postgres (подтвердить в логах/таблицах), не sqlite-дефолт.
- [ ] pydantic-settings продолжает читать конфиг (case-insensitive) — не сломать локальный запуск.
- [ ] Весь CI начисто зелёный.

## Ожидаемые артефакты
- `.env.example`, `docker-compose.yml`, `docker/entrypoint.sh`, `docs/deployment.md`, `README.md`.

## Ограничения / заметки
- Только конфиг/деплой/доки, без изменения логики. Перед `done`: полный CI, фактическая проверка
  `docker compose config`/сборки (привести вывод в отчёте), отчёт, лог, push.

## Зависимости
Зависит от: TASK-0022
