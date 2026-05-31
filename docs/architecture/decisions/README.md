# Architecture Decision Records (ADR)

Журнал значимых решений. Каждое решение — отдельный файл `ADR-XXXX-краткое-имя.md`
по шаблону [`_template.md`](_template.md). Решения **не удаляются**: устаревшие
помечаются статусом `Superseded by ADR-YYYY`.

| ADR | Решение | Статус |
|-----|---------|--------|
| [ADR-0001](ADR-0001-collaboration-framework.md) | Фреймворк совместной работы (handoff через git, GitHub как источник правды) | Accepted |
| [ADR-0002](ADR-0002-tech-stack.md) | Технологический стек бота | Accepted |
| [ADR-0003](ADR-0003-data-layer.md) | Слой данных: SQLAlchemy 2.0 async + Alembic | Accepted |
| [ADR-0004](ADR-0004-timezones.md) | Часовые пояса: поле `tz`, дефолт Europe/Moscow | Accepted |
| [ADR-0005](ADR-0005-notification-engine.md) | Движок уведомлений: свип по БД + `sent_reminders`, «Отложить» | Accepted |
| [ADR-0006](ADR-0006-charge-lifecycle-amount.md) | Жизненный цикл списания (мягкое закрытие) и сумма (Decimal) | Accepted |
| [ADR-0007](ADR-0007-delivery-long-polling.md) | Доставка апдейтов: long polling в v1 | Accepted |

Все ключевые архитектурные вопросы перед M1 закрыты ADR-0003…0007 (SESSION-2026-06-01-01).
