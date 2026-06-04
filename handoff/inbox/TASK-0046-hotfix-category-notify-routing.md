---
id: TASK-0046
title: "BLOCKER: добавление канала для категории зависает — порядок callback-фильтров category_notify_ шадовит add/remove"
milestone: M7
status: inbox
priority: high
created_by: architect
created_at: 2026-06-04T02:00:00Z
depends_on: [TASK-0043]
---

# TASK-0046: Хотфикс — зависание «Добавить канал/группу» (callback routing)

## Симптом (отзыв пользователя)
В настройках категории → «🔔 Каналы для напоминаний» → «➕ Добавить канал/группу» **ничего не
происходит, бот зависает** (спиннер на кнопке не гаснет, ввод chat_id не запрашивается).

## Корневая причина (подтверждено по коду)
Класс бага TASK-0008 (порядок callback-фильтров). В `handlers/categories.py` три хэндлера:
- стр. 204 `category_notify_list` — `F.data.startswith("category_notify_")` (ШИРОКИЙ), **зарегистрирован первым**;
- стр. 233 `category_notify_remove` — `startswith("category_notify_remove_")`;
- стр. 262 `category_notify_add_start` — `startswith("category_notify_add_")`.

Callbacks (keyboards.py): `category_notify_{id}`, `category_notify_remove_{id}_{tid}`,
`category_notify_add_{id}` — все начинаются с `category_notify_`.

В aiogram внутри роутера выполняется **первый** хэндлер, чей фильтр прошёл, и распространение
останавливается. Для `category_notify_add_{id}` первым проходит широкий фильтр стр. 204 →
вызывается `category_notify_list`, который упирается в guard `if any(x in data for x in
("_remove_","_add_")): return`. Но `return` в aiogram **не делегирует** следующему хэндлеру —
апдейт уже считается обработанным. Итог: `category_notify_add_start` (и `remove`) **никогда не
вызываются**, `set_state(CategoryStates.notify_chat_id)` не происходит, а в guard-ветке нет
`callback.answer()` → спиннер висит. Аналогично сломано удаление цели.

## Решение
- **Зарегистрировать специфичные хэндлеры РАНЬШЕ широкого:** `category_notify_add_` и
  `category_notify_remove_` — выше `category_notify_list`. (В одном роутере порядок = порядок
  определения в файле.)
- Удалить нерабочий guard-`return` из `category_notify_list` (он создавал ложное ощущение защиты).
  При желании дополнительно сузить широкий фильтр, но первичный фикс — порядок.
- Гарантировать `callback.answer()` на всех ветках (анти-залипание спиннера).
- (Рекомендация, в рамках этой задачи) перепроверить ПРОЧИЕ широкие `startswith` в проекте на
  тот же шадовинг: напр. `charge_confirm_` vs `charge_confirm_create`/`charge_confirm_delete_`
  (уже разводили в TASK-0040), `category_confirm_`, `charge_*`. Где есть «префикс-в-префиксе» —
  специфичные регистрировать первыми.

## Критерии приёмки (проверяемые)
- [ ] «➕ Добавить канал/группу» открывает запрос ввода chat_id (FSM `CategoryStates.notify_chat_id`),
      затем валидный chat_id добавляется и показывается обновлённый список. Удаление цели работает.
- [ ] **Регрессионный тест на уровне роутера** через `dp.feed_update` (НЕ прямой вызов хэндлера):
      реальные callbacks `category_notify_{id}`, `category_notify_add_{id}`,
      `category_notify_remove_{id}_{tid}` маршрутизируются в правильные хэндлеры; `add` переводит FSM
      в `notify_chat_id`. Тест должен падать на текущем (сломанном) порядке.
- [ ] Нет «висящего» спиннера: `callback.answer()` вызывается во всех ветках.
- [ ] Весь CI начисто зелёный.

## Ожидаемые артефакты
- `src/wrbot/bot/handlers/categories.py` (переупорядочить хэндлеры, убрать мёртвый guard),
  тесты (router-level через feed_update).

## Ограничения / заметки
- Блокирующий баг релиза v0.3.0 → после фикса хотфикс-релиз **v0.3.1**.
- Урок процесса: handler-тесты, дёргающие функцию напрямую, НЕ ловят шадовинг по порядку фильтров —
  обязателен router-level e2e (см. `docs/workflow/executor-guide.md`, чек-лист живого потока).
- Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0043 (вводил этот UI).
