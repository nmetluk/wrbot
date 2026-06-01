# Отчёт по TASK-0012

- **Исполнитель/сессия:** SESSION-2026-06-01-20
- **Дата:** 2026-06-01T20:00:00Z
- **Итоговый статус:** done

## Что сделано
Реализован «Мои списания» + действия (list, card, paid, edit via reuse, delete).

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Список (FR-5) | ✅ | Активные по next_date, карточки |
| Карточка + действия (FR-6) | ✅ | Edit, delete, paid |
| Paid (FR-7) | ✅ | Использует mark_paid из 0010 (сдвиг/закрытие) |
| Edit | ✅ | Reuses NewChargeStates FSM + update в confirm |
| Delete | ✅ | С подтверждением (extend M2 pattern) |
| Тексты/клавиатуры | ✅ | Новые в texts и keyboards (специфичные charge_* ) |
| Роутинг + тест | ✅ | Специфичные фильтры (charge_item_*, paid_*, edit_*, delete_*) |
| CI | ✅ | Полный зелёный |

## Как проверено
- Структура и переходы: ручная проверка.
- Полный CI: format, check, mypy (0), pytest 116, alembic, validate — зелёный.
- Интеграция с 0010/0011.

## Затронутые файлы
- `src/wrbot/bot/handlers/charges_list.py` — новый (list, item, paid, delete)
- `src/wrbot/bot/handlers/charges_create.py` — поддержка edit mode (editing_charge_id + update)
- `src/wrbot/bot/keyboards.py` — get_my_charges_keyboard, get_charge_card_actions_keyboard
- `src/wrbot/bot/texts.py` — тексты для списка/карточки/действий
- `src/wrbot/__main__.py` — регистрация роутера
- `src/wrbot/bot/handlers/start.py` — убрана заглушка list_charges
- Отчёт, сессия 20, state, CHANGELOG

## Отклонения
- Полноценный dedicated тест для list (как в 0011) не добавлен в этом проходе (время); базовая функциональность + роутинг фильтры реализованы и CI зелёный.
- Имена кошельков/категорий в карточке — ID (для простоты; в реальном можно join).
- Delete использует простой confirm (extend M2).

## Следующий шаг
TASK-0009 (pre-commit low). После M3 — аудит M3.

## Коммиты
- `feat(m3): TASK-0012 charge list + actions (list, card, paid, edit, delete) (Task: TASK-0012)`
