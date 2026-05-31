# Модель данных

Источник — ТЗ §2. Все пользовательские данные изолированы по `tg_id` (FR-13).

## Сущности и связи

```
User (tg_id) 1───* Wallet
     │         1───* Category
     │         1───* Charge *───1 Wallet
                         *───0..1 Category
```

## Таблицы (схема зафиксирована ADR-0003…0006; реализуется в TASK-0001 через Alembic)

Слой данных — SQLAlchemy 2.0 async + Alembic (ADR-0003). Все внутренние временные
метки — в UTC (ADR-0004).

### users
| Поле | Тип | Прим. |
|------|-----|-------|
| `tg_id` | INTEGER PK | Telegram user_id |
| `notify_time` | TIME/TEXT | «HH:MM», локальное время в `tz`, по умолчанию `10:00` |
| `tz` | TEXT | IANA-пояс, по умолчанию `Europe/Moscow` (ADR-0004) |
| `global_days` | JSON | массив дней-напоминаний, по умолчанию `[5,3,1]` |
| `created_at` | TIMESTAMP | UTC |

### wallets
| Поле | Тип | Прим. |
|------|-----|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK→users.tg_id | |
| `name` | TEXT | «Тинькофф Black», «Сбер»… |

### categories
| Поле | Тип | Прим. |
|------|-----|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK→users.tg_id | |
| `name` | TEXT | «Подписки», «ЖКХ», «Кредиты»… |

### charges
| Поле | Тип | Прим. |
|------|-----|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK→users.tg_id | |
| `name` | TEXT | |
| `amount` | NUMERIC(precision) | Decimal, 2 знака; одна валюта (₽) в v1 (ADR-0006) |
| `wallet_id` | INTEGER FK→wallets.id | |
| `category_id` | INTEGER FK→categories.id NULL | опционально |
| `next_date` | DATE | дата следующего списания |
| `period` | TEXT/ENUM | `once`/`monthly`/`quarterly`/`yearly` |
| `individual_days` | JSON NULL | переопределяет `global_days`; `null` = глобальные; `[]` = выключено |
| `status` | TEXT/ENUM | `active`/`done`, по умолчанию `active` (ADR-0006) |
| `paid_at` | TIMESTAMP NULL | UTC, момент закрытия одноразового (ADR-0006) |
| `snoozed_until` | DATE NULL | отметка «Отложить» — повтор напоминания (ADR-0005) |
| `created_at` | TIMESTAMP | UTC |

### sent_reminders (идемпотентность уведомлений, ADR-0005)
| Поле | Тип | Прим. |
|------|-----|-------|
| `id` | INTEGER PK | |
| `charge_id` | INTEGER FK→charges.id | каскад при удалении списания |
| `target_date` | DATE | дата платежа, к которой относится напоминание |
| `days_before` | INTEGER | за сколько дней (5/3/1/…) |
| `sent_at` | TIMESTAMP | UTC |
| | UNIQUE (`charge_id`,`target_date`,`days_before`) | защита от дублей/рестарта |

## Правила домена
- **Сдвиг даты (FR-7, ADR-0006):** при «Оплачено» периодического — `next_date` += период
  с клампом к последнему дню месяца, если числа нет (напр. 31-е в феврале); одноразовое —
  `status=done`, `paid_at=now`, **не удаляется** (история для статистики §6).
- **Дни напоминаний (FR-11):** действующие дни = `individual_days` если задан, иначе
  `global_days`; `[]` = напоминания выключены.
- **«Отложить» (ADR-0005):** не меняет `next_date`; ставит `snoozed_until` = следующий день,
  напоминание повторяется в `notify_time`.
- **Каскад:** удаление кошелька с привязанными списаниями — поведение определить в M2
  (запрет с предупреждением vs каскад); по умолчанию — запрет, если есть активные списания.

## Миграции
SQLite на старте, путь к PostgreSQL учтён через SQLAlchemy 2.0 async + Alembic (ADR-0003):
типы (NUMERIC, JSON↔JSONB), autoincrement, версионируемые миграции. Никаких `CREATE TABLE`
в коде — только Alembic.
