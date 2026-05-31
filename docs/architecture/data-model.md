# Модель данных

Источник — ТЗ §2. Все пользовательские данные изолированы по `tg_id` (FR-13).

## Сущности и связи

```
User (tg_id) 1───* Wallet
     │         1───* Category
     │         1───* Charge *───1 Wallet
                         *───0..1 Category
```

## Таблицы (предлагаемая схема; финализируется в TASK по БД)

### users
| Поле | Тип | Прим. |
|------|-----|-------|
| `tg_id` | INTEGER PK | Telegram user_id |
| `notify_time` | TEXT/TIME | «HH:MM», по умолчанию `10:00` |
| `global_days` | TEXT(JSON) | массив дней-напоминаний, по умолчанию `[5,3,1]` |
| `created_at` | TEXT/TIMESTAMP | |

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
| `amount` | NUMERIC | формат/валюта — см. открытые вопросы |
| `wallet_id` | INTEGER FK→wallets.id | |
| `category_id` | INTEGER FK→categories.id NULL | опционально |
| `next_date` | TEXT/DATE | дата следующего списания |
| `period` | TEXT/ENUM | `once`/`monthly`/`quarterly`/`yearly` |
| `individual_days` | TEXT(JSON) NULL | переопределяет `global_days`; `null` = глобальные; `[]` = выключено |

## Правила домена
- **Сдвиг даты (FR-7):** при «Оплачено» `next_date` += период; `once` закрывается
  (помечается завершённым/удаляется — решить в ADR).
- **Дни напоминаний (FR-11):** действующие дни = `individual_days` если задан, иначе `global_days`.
- **Каскад:** удаление кошелька с привязанными списаниями — поведение определить (запрет/каскад).

## Миграции
SQLite на старте, путь к PostgreSQL должен быть учтён (типы, autoincrement, JSON).
Стратегия миграций — в ADR по слою данных.
