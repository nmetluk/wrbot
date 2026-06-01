# Развёртывание wrbot (Docker)

Этот документ описывает запуск бота в production с помощью Docker (M5, TASK-0022).

## Быстрый старт (SQLite)

```bash
# 1. Скопируйте и заполните переменные окружения
cp .env.example .env
# Отредактируйте .env — обязательно укажите bot_token

# 2. Запустите
docker compose up -d --build

# 3. Посмотреть логи
docker compose logs -f bot
```

## С PostgreSQL (рекомендуется для production)

```bash
docker compose --profile postgres up -d --build
```

В `.env` укажите:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/wrbot
```

## Основные файлы

- `Dockerfile` — сборка образа с uv (воспроизводимые зависимости из `uv.lock`)
- `docker/entrypoint.sh` — автоматически выполняет `alembic upgrade head` перед запуском бота
- `docker-compose.yml` — основная конфигурация (restart: unless-stopped, volume для данных)

## Проверка здоровья

```bash
docker compose ps          # статус контейнера
docker compose logs bot    # последние логи
```

Контейнер имеет простой healthcheck. Для production рекомендуется добавить мониторинг (Prometheus, Grafana, или простой HTTP health endpoint в будущем).

## Обновление

```bash
docker compose pull
docker compose up -d --build
```

Миграции применяются автоматически при каждом старте контейнера (идемпотентно).

## Важные замечания

- **Секреты**: Никогда не коммитьте `.env`. Используйте `env_file` в compose.
- **Данные**: SQLite хранится в `./data/` на хосте (том).
- **Логи**: По умолчанию внутри контейнера. Для persistence раскомментируйте volume в compose.
- **Ресурсы**: Для небольшого количества пользователей достаточно 512MB RAM.

## Откат

```bash
docker compose down
# или с удалением данных (осторожно!)
docker compose down -v
```

После отката можно поднять заново — миграции восстановят структуру БД.
