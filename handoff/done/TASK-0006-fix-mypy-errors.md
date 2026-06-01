---
id: TASK-0006
title: Исправить mypy ошибки типизации
milestone: M2
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T04:47:15Z
depends_on: [TASK-0005]
---

# TASK-0006: Исправить mypy ошибки типизации

## Цель
Исправить 64 ошибки mypy в handlers и keyboards для прохождения CI. Без этого M2 не может быть принят.

## Контекст
- Аудит SESSION-2026-06-01-11: mypy падает с 64 ошибками
- ТЗ: §5 (NFR-4 — расширяемость, качество кода)
- Связанные ADR: ADR-0003 (слои доступа к данным)

## Типы ошибок
1. **union-attr (40+ шт)**: доступ к атрибутам `Message|InaccessibleMessage|None` без проверки на None
   - Файлы: `handlers/wallets.py`, `handlers/categories.py`, `handlers/settings.py`, `handlers/start.py`
   - Пример: `callback.message.edit_text()` — `message` может быть `InaccessibleMessage|None`

2. **type-arg (4 шт)**: `dict` без параметров типов
   - Файлы: `keyboards.py` (строки 58, 112), handlers (dict в callback handler args)
   - Решение: заменить `dict` на `dict[str, Any]`

3. **assignment (2 шт)**: присваивание `Wallet|None` переменной типа `Wallet`
   - Файлы: `handlers/wallets.py:142`, `handlers/categories.py:142`
   - Решение: добавить проверку на None или изменить тип переменной

4. **arg-type (5+ шт)**: передача `dict[Any, Any]` вместо `AsyncSession`
   - Файлы: `handlers/wallets.py`, `handlers/categories.py`, `handlers/settings.py`
   - Причина: middleware кладёт сессию в `data: dict[str, Any]`, а типизация для `**handler_data: dict` теряет типы

## Критерии приёмки
- [ ] `uv run mypy src/wrbot` проходит без ошибок
- [ ] Все handlers/keyboards типизированы корректно
- [ ] CI зелёный (ruff + mypy + pytest + validate)
- [ ] Функциональность не изменилась (pytest still passes)

## Ожидаемые артефакты
- Код: исправления в `src/wrbot/bot/handlers/*.py`, `src/wrbot/bot/keyboards.py`

## Ограничения / заметки
- Не менять логику, только типы
- Сохранить существующие паттерны (middleware DI, FSM)
- Для `**handler_data: dict`可以考虑 использовать TypedDict или явные типы в middleware

## Зависимости
Зависит от: TASK-0005 (UI справочников)
