---
id: TASK-0030
title: "E2E через aiogram Dispatcher (feed_update) — заменить placeholder, автоматизируемая замена ручной QA"
milestone: M5
status: inbox
priority: high
created_by: architect
created_at: 2026-06-03T02:00:00Z
depends_on: [TASK-0027, TASK-0029]
---

# TASK-0030: Реальный e2e через Dispatcher (feed_update)

## Цель
Дать автоматизируемую замену «ручной QA в Telegram» (исполнитель не может кликать в живом
клиенте): прогон апдейтов через **реальный `Dispatcher` + middleware + роутеры + реальную
SQLite + mock `Bot`**. Заменить пустой `tests/test_e2e_smoke.py` (`assert True`) настоящими сценариями.

## Контекст / приоритет
- **Severity: high (release gate).** TASK-0028 (ручная QA) исполнителем физически не выполнима —
  отчёт `QA-MANUAL-2026-06-03.md` это честно фиксирует (code review + CI, не live). `test_e2e_smoke.py`
  до сих пор заглушка. Нужен реальный сквозной автотест.
- Уже есть точечные интеграционные тесты: `test_fsm_session_lifecycle.py` (middleware+DB),
  `test_callback_routing.py` (router introspection). Эта задача связывает всё через Dispatcher.

## Критерии приёмки (проверяемые)
- [ ] `tests/test_e2e_smoke.py` (или новый `test_e2e_dispatcher.py`) использует
      `await dp.feed_update(bot, update)` с **реально зарегистрированными** роутерами и
      `DbSessionMiddleware` (как в `__main__`), реальной временной SQLite (через миграцию) и
      `Bot`-моком (AsyncMock), записывающим `send_message`/`edit_*`/`answer`.
- [ ] **Сценарии (минимум), с проверкой ПЕРСИСТЕНТНОСТИ в БД, а не только ответов бота:**
      1) `/start` → меню (4 кнопки в ответе);
      2) создать кошелёк через FSM (Message-апдейты) → запись есть в `wallets` (новой сессией);
      3) создать списание полным FSM → запись в `charges`; видно в «Мои списания»;
      4) «Оплачено» (periodic) → `next_date` сдвинут; (once) → `status=done`;
      5) глобальные уведомления: сменить время/дни → значения в `users` обновлены;
      6) изоляция: апдейты от user B не видят/не меняют данные user A.
- [ ] Каждый шаг — через отдельный `feed_update` (как отдельные апдейты Telegram), т.е.
      реальный цикл middleware (открыл→коммит→закрыл) между шагами — это ловит классы багов
      TASK-0008 (роутинг) и TASK-0027 (сессия).
- [ ] Placeholder `assert True` удалён. Весь CI начисто зелёный (`uv run` ruff/mypy/pytest/alembic/validate).

## Ожидаемые артефакты
- Тесты: `tests/test_e2e_dispatcher.py` (или переписанный `test_e2e_smoke.py`), общий фикстур-helper
  для сборки `Dispatcher` + middleware + mock Bot + временной БД.

## Ограничения / заметки
- Это НЕ замена живой проверки владельцем, а её автоматизируемая часть. Живой смоук — за владельцем
  (`QA-MANUAL-*.md`). Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0027, TASK-0029
