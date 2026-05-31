# Changelog

All notable changes to wrbot will be documented in this file.

## [0.1.0] - 2026-06-01

### Added
- Python/Aiogram 3.x project skeleton
- SQLAlchemy 2.0 async ORM with 5 tables (users, wallets, categories, charges, sent_reminders)
- Alembic migrations with initial schema
- Bot entry point with long polling (ADR-0007)
- /start command with inline menu (➕ Новое списание, 📋 Мои списания, ⚙️ Настройки, ❔ Помощь)
- /help and /cancel commands
- Configuration from environment (.env support)
- Structured logging to logs/ directory
- APScheduler integration stub
- Domain models (dataclasses) and service stubs
- Pytest tests (8 smoke tests)
- CI configuration (ruff, mypy, pytest)
- Documentation: README with local run instructions

### Technical
- Python 3.11+ required
- aiogram 3.13+, APScheduler 3.11+
- SQLAlchemy 2.0 async with asyncpg/aiosqlite
- Alembic for migrations
- ruff for linting, mypy for type checking
