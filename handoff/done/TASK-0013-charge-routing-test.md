---
id: TASK-0013
title: Router-тест для callback'ов списаний (charge_*)
milestone: M3
status: inbox
priority: low
created_by: architect
created_at: 2026-06-01T19:30:00Z
depends_on: [TASK-0012]
---

# TASK-0013: Регрессионный router-тест для charge_* callback'ов

## Цель
Закрыть пробел, отмеченный в AUDIT-M3: фильтры `charge_*` корректны, но не покрыты
тестом через роутер (как для wallet/category в `test_callback_routing.py`).

## Контекст
- AUDIT-M3-2026-06-01 (SESSION-2026-06-01-22), замечание #1 (minor).
- Урок TASK-0008: проверять диспетчеризацию роутера, а не только прямой вызов хэндлера.

## Критерии приёмки (проверяемые)
- [ ] В `tests/test_callback_routing.py` (или новом файле) добавлены тесты, что через
      реальные зарегистрированные фильтры роутеров `charges_create`/`charges_list`:
      `new_charge` → создание; `list_charges` → список; `charge_item_<id>` → карточка;
      `charge_paid_<id>` → оплата; `charge_delete_<id>`/`charge_confirm_<id>` → удаление/подтверждение;
      и НЕ перехватываются чужими хэндлерами.
- [ ] Тест устойчив к будущему добавлению широкого `startswith("charge_")` (падал бы на нём).
- [ ] Весь CI начисто без BOT_TOKEN зелёный (ruff format/check, mypy, pytest, alembic, validate).

## Ожидаемые артефакты
- Тесты: дополнения в `tests/test_callback_routing.py`.

## Ограничения / заметки
- Только тесты; код хэндлеров менять не требуется (фильтры уже корректны). Low priority —
  можно сделать до старта M4 или параллельно. Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0012
