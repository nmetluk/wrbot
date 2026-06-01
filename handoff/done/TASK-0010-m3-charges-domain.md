---
id: TASK-0010
title: "M3: доменная логика дат + ChargeRepository (сдвиг/оплачено)"
milestone: M3
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T16:30:00Z
depends_on: [TASK-0005]
---

# TASK-0010: Доменная логика дат + ChargeRepository

## Цель
Заложить фундамент M3: расчёт следующей даты с клампом конца месяца и репозиторий
списаний, включая «отметить оплачено» (сдвиг периода / мягкое закрытие). **Без бот-UI.**

## Контекст
- ТЗ §3.2 (оплачено → сдвиг), §2 (поля списания), §1.3 (изоляция tg_id).
- Требования: FR-4 (периоды), FR-7 (сдвиг/закрытие), FR-13 (изоляция).
- ADR: **ADR-0006** (мягкое закрытие `status=done`/`paid_at`, кламп конца месяца, сумма Decimal),
  ADR-0003 (репозитории), ADR-0005 (`snoozed_until` — пока не трогаем, это M4).
- Готово: модели `Charge` (`src/wrbot/db/models.py`, `src/wrbot/models.py`), enum
  `ChargePeriod`/`ChargeStatus`; заглушка `src/wrbot/services/dates.py:calculate_next_date`.
  Таблица `charges` уже в миграции (новой миграции НЕ требуется).

## Критерии приёмки (проверяемые)
- [ ] **`calculate_next_date(current, period)`** реализован: `monthly` +1 мес, `quarterly` +3,
      `yearly` +12, с **клампом к последнему дню месяца** (31 янв → 28/29 фев; 31 → 30 и т.п.);
      `once` не сдвигается (обрабатывается как закрытие). Покрыто тестами на edge-кейсы
      (конец месяца, високосный год, кварталы через границу года).
- [ ] **ChargeRepository** (изоляция по `user_id`, FR-13):
      `create(...)`, `list_active_by_user(user_id)` (только `status=active`, сортировка по `next_date`),
      `get(user_id, charge_id)`, `update(...)`, `delete(user_id, charge_id)`,
      **`mark_paid(user_id, charge_id)`**: для периодических — `next_date = calculate_next_date(...)`,
      статус остаётся `active`; для `once` — `status=done`, `paid_at=now (UTC)`. Запись не удаляется.
- [ ] Валидация/парсинг суммы (Decimal, 2 знака, > 0) и периода — в сервисе (например `services/charges.py`),
      доменные ошибки по образцу `services/reference.py`.
- [ ] Лимит на число активных списаний на пользователя — в конфиг (`max_charges`, разумный дефолт).
- [ ] **Тесты** (через реальную миграцию на временной SQLite): даты (edge-кейсы), CRUD,
      изоляция tg_id, `mark_paid` для периодического (сдвиг) и `once` (done+paid_at), лимит.
      Моки — со `spec`/autospec.
- [ ] Весь CI начисто без BOT_TOKEN зелёный: `ruff format --check src tests`, `ruff check src tests`,
      `mypy src`, `pytest`, `alembic upgrade head`, `python scripts/validate.py`.

## Ожидаемые артефакты
- Код: `src/wrbot/services/dates.py` (реализация), `src/wrbot/repositories/charges.py`,
  `src/wrbot/services/charges.py` (валидация/лимиты), `config.py` (`max_charges`).
- Тесты: `tests/test_dates.py`, `tests/test_repositories_charges.py`.

## Ограничения / заметки
- Без бот-хэндлеров и клавиатур (это TASK-0011/0012). Только домен + данные.
- `snoozed_until`/уведомления — НЕ реализовывать (M4).
- Все временные метки — UTC (ADR-0004). Перед `done`: полный прогон CI (см. executor-guide), отчёт, лог, push.

## Зависимости
Зависит от: TASK-0005
