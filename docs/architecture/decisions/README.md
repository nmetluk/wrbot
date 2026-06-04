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
| [ADR-0008](ADR-0008-admin-observability.md) | Админ-канал и подсистема наблюдаемости (M6) | Accepted |
| [ADR-0009](ADR-0009-backups.md) | Стратегия бэкапов: ежечасно, ротация 36, VACUUM INTO/pg_dump (M6) | Accepted |
| [ADR-0010](ADR-0010-audit-log.md) | Аудит-лог действий (таблица + дубль критичных в канал) (M6) | Accepted |
| [ADR-0011](ADR-0011-wallet-icons.md) | Иконки кошельков/карт — эмодзи из пресета (M7) | Accepted |
| [ADR-0012](ADR-0012-category-notify-targets.md) | Дубль напоминаний в каналы/группы по категориям (M7) | Accepted |
| [ADR-0013](ADR-0013-currencies.md) | Валюты списаний: bundled ISO 4217, валюта на списание, пресеты+список/поиск (M8) | Accepted |

Все ключевые архитектурные вопросы перед M1 закрыты ADR-0003…0007 (SESSION-2026-06-01-01).
M6 (наблюдаемость/бэкапы/аудит) — ADR-0008…0010 (SESSION-2026-06-03-03).
M7 (доработки по отзывам) — ADR-0011…0012 (SESSION-2026-06-03-16).
