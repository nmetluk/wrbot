---
id: TASK-0018
title: "M4 BLOCKER: mypy 12 ошибок в handlers/reminders.py (CI красный)"
milestone: M4
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T21:30:00Z
depends_on: [TASK-0015]
---

# TASK-0018: mypy-зелёный handlers/reminders.py

## Цель
Сделать `mypy src` зелёным: 12 ошибок в `src/wrbot/bot/handlers/reminders.py`.

## Контекст / приоритет
- **Severity: BLOCKER (CI).** `mypy src` падает (12 ошибок), CI-шаг mypy красный.
  Отчёты 0015/0016 гоняли mypy по своим файлам, а не `mypy src` — поэтому пропустили.
- Тот же класс, что чинили в TASK-0006.

## Найдено (прогон `mypy src`)
- `reminders.py:76` `union-attr`: `callback.data.split` на `str | None`.
- `reminders.py:95` (и др.) `union-attr`: `callback.message.edit_text` на `Message | InaccessibleMessage | None`.
- Всего 12 ошибок в этом файле.

## Критерии приёмки (проверяемые)
- [ ] `mypy src` — `Success`, 0 ошибок (--strict).
- [ ] Сужение типов сделано корректно: `isinstance(callback.message, Message)` перед `.edit_text`;
      проверка `callback.data`/`callback.from_user` на `None` перед использованием. Без слепых `# type: ignore`
      (точечный ignore только там, где значение гарантировано фильтром, с комментарием).
- [ ] Функциональность хэндлеров уведомлений не изменилась (pytest зелёный).
- [ ] Весь CI начисто без BOT_TOKEN зелёный (ruff format/check, **mypy src**, pytest, alembic, validate).

## Ожидаемые артефакты
- Код: `src/wrbot/bot/handlers/reminders.py`.

## Ограничения / заметки
- Только типы/сужение, без смены логики. Перед `done`: прогнать именно `mypy src` (весь пакет), отчёт, лог, push.

## Зависимости
Зависит от: TASK-0015
