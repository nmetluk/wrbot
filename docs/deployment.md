# Развёртывание wrbot (Docker)

Полная инструкция по запуску бота 24/7 с помощью Docker (M5, TASK-0022 + TASK-0023).

## Требования
- Docker и Docker Compose v2+
- Токен бота от @BotFather
- (Опционально) сервер PostgreSQL для production

## Быстрый старт (SQLite — для теста/небольших объёмов)

```bash
# 1. Подготовьте окружение
cp .env.example .env
# Обязательно заполните BOT_TOKEN (и DATABASE_URL если нужно; используйте UPPERCASE)

# 2. Запустите
docker compose up -d --build

# 3. Проверьте
docker compose ps
docker compose logs -f bot
```

Бот будет автоматически применять миграции при каждом старте контейнера.

## Production: PostgreSQL

```bash
docker compose --profile postgres up -d --build
```

В `.env` укажите (UPPERCASE имена переменных):

```env
BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/wrbot
POSTGRES_DB=wrbot
POSTGRES_USER=wrbot
POSTGRES_PASSWORD=strong-password-here
# DEFAULT_TIMEZONE=Europe/Moscow (опционально)
# LOG_LEVEL=INFO (опционально)
```

## Основные файлы

- `Dockerfile` — Python 3.11-slim + uv (воспроизводимая установка из `uv.lock`), non-root пользователь.
- `docker/entrypoint.sh` — запускает `alembic upgrade head`, затем `python -m wrbot`.
- `docker-compose.yml` — `restart: unless-stopped`, volume `./data`, `env_file: .env` (UPPERCASE vars), healthcheck, опциональный профиль `postgres`.

## Полный цикл деплоя

1. Настройте `.env` (UPPERCASE: BOT_TOKEN, DATABASE_URL и т.д.; никогда не коммитьте!).
2. `docker compose up -d --build`
3. Проверьте логи и статус.
4. При обновлении кода: `git pull && docker compose up -d --build`
5. Миграции применяются автоматически (идемпотентно).

## Переход с SQLite на PostgreSQL

1. Остановите бота.
2. Выгрузите данные (если нужно).
3. Измените `DATABASE_URL` (и другие UPPER) в `.env`.
4. `docker compose --profile postgres up -d --build`
5. Проверьте, что данные перенесены (или начните с чистой БД).

## Мониторинг и здоровье

```bash
docker compose ps
docker compose logs --tail=100 bot
docker compose logs -f bot
```

В compose настроен базовый healthcheck. Для серьёзного мониторинга добавьте Prometheus + Grafana или внешний uptime checker.

## Откат и очистка

```bash
docker compose down          # остановить
docker compose down -v       # остановить + удалить volumes (данные!)
```

## Полезные советы

- Секреты хранятся только в `.env` (монтируется через `env_file`).
- Логи внутри контейнера. Для постоянного хранения раскомментируйте volume в compose.
- Ресурсы: для 1–50 пользователей обычно хватает 512–1024 МБ RAM.

Более детальные инструкции и troubleshooting — в этом же файле (обновляйте по мере необходимости).
