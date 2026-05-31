# Changelog

История версий wrbot для пользователей. Формат основан на [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-06-01

### Added
- Скелет Python/Aiogram 3.x проекта
- SQLAlchemy 2.0 async ORM с 5 таблицами (users, wallets, categories, charges, sent_reminders)
- Alembic миграции с начальной схемой
- Long polling для получения апдейтов от Telegram (ADR-0007)
- Команда `/start` с инлайн-меню (➕ Новое списание, 📋 Мои списания, ⚙️ Настройки, ❔ Помощь)
- Команды `/help` и `/cancel`
- Конфигурация из переменных окружения (.env support)
- Структурированное логирование в `logs/`
- Заглушки для APScheduler
- Доменные модели (dataclasses) и сервисов
- Pytest тесты
- CI: ruff, mypy, pytest, alembic, validate.py

### Technical
- Python 3.11+ требуется
- aiogram 3.13+, APScheduler 3.11+
- SQLAlchemy 2.0 async с asyncpg/aiosqlite
- Alembic для миграций
- ruff для линтинга, mypy для типизации
