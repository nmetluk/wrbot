---
id: TASK-0008
title: "M2 critical: порядок callback-фильтров ломает CRUD (add/rename/delete)"
milestone: M2
status: inbox
created_by: architect
created_at: 2026-06-01T11:30:00Z
depends_on: [TASK-0005]
---

# TASK-0008: Маршрутизация callback'ов справочников (критический функциональный баг)

## Цель
Устранить перехват специфичных callback'ов широким фильтром в хэндлерах кошельков и
категорий, из-за которого ломается добавление/переименование/удаление. Это блокирует
реальное использование M2, но **не ловится mypy и текущими 92 юнит-тестами** (они зовут
хэндлеры напрямую, минуя диспетчеризацию роутера).

## Контекст
- ТЗ §3.3 (CRUD кошельков/категорий), FR-8, FR-9.
- Найдено при ревью M2 (SESSION-2026-06-01-12); не входит в TASK-0006 (mypy)/TASK-0007 (ruff).
- Файлы: `src/wrbot/bot/handlers/wallets.py`, `categories.py`, `keyboards.py`.

## Суть бага (подтверждено чтением кода)
`handlers/wallets.py` регистрирует ПЕРВЫМ:
```python
@router.callback_query(F.data.startswith("wallet_"))   # wallet_details
async def wallet_details(callback): wallet_id = int(callback.data.split("_")[1])
```
Кнопки из `keyboards.py`: `wallet_add`, `wallet_rename_<id>`, `wallet_delete_<id>`,
`wallet_confirm_<id>` — **все начинаются с `wallet_`**. В aiogram внутри роутера выигрывает
ПЕРВЫЙ подходящий хэндлер → нажатие «Добавить» уходит в `wallet_details`, где
`int("wallet_add".split("_")[1]) == int("add")` → `ValueError`. Итог: add/rename/delete не работают.
**То же самое в `categories.py`** (`category_*`).

## Критерии приёмки (проверяемые)
- [ ] Нажатие «➕ Добавить», «✏️ Переименовать», «🗑 Удалить», подтверждение удаления —
      попадают в свои хэндлеры (не в `*_details`) и работают. Аналогично для категорий.
- [ ] Фильтр деталей сделан специфичным (например, item-callback `wallet_item_<id>` /
      `category_item_<id>`, либо явные исключения префиксов add/rename/delete/confirm),
      `keyboards.py` обновлён согласованно.
- [ ] **Тест диспетчеризации через роутер** (не прямой вызов хэндлера): прогон
      `CallbackQuery` с `data` = `wallet_add`/`wallet_rename_<id>`/`wallet_delete_<id>` и
      `category_*` доходит до правильного хэндлера. Тест должен падать на текущем коде.
- [ ] CI начисто без BOT_TOKEN зелёный: `ruff format --check src tests`, `ruff check src tests`,
      `mypy src`, `pytest`, `alembic upgrade head`, `python scripts/validate.py`.

## Ожидаемые артефакты
- Код: `handlers/wallets.py`, `handlers/categories.py`, `keyboards.py`.
- Тесты: новый тест маршрутизации через роутер (`tests/test_callback_routing.py` или аналог).

## Ограничения / заметки
- Скоординируй с TASK-0006/0007 (один зелёный гейт в итоге). Бизнес-логику M3 не трогать.
- Реальную проверку в Telegram желательно сделать руками (UX-баги ускользают от unit-тестов).
- Перед `done`: отчёт, лог сессии (уникальный ID), state, push.

## Зависимости
Зависит от: TASK-0005
