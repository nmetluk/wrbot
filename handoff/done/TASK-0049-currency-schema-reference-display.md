---
id: TASK-0049
title: "Валюты (1/2): схема Charge.currency + User.last_currency, загрузчик справочника, валютно-зависимое отображение (убрать зашитый ₽)"
milestone: M8
status: inbox
priority: high
created_by: architect
created_at: 2026-06-04T05:30:00Z
depends_on: []
---

# TASK-0049: Фундамент валют — схема, справочник, отображение (ADR-0013)

## Цель (срочный отзыв, часть 1/2)
Дать списаниям валюту и показывать её везде вместо зашитого «₽». Сам выбор валюты в потоке —
в TASK-0050 (эта задача — модель данных, справочник и отображение).

## Готовое сырьё (уже в репозитории, положено архитектором)
- `src/wrbot/data/iso4217.csv` — справочник ISO 4217 (источник datasets/currency-codes).
- `src/wrbot/data/currencies.json` — сгенерированный список: `presets=[RUB,EUR,USD,KZT,KGS]`,
  `default=RUB`, `currencies=[{code,name,minor,(symbol)}]` (153 активные валюты).

## Реализация
- **Миграция Alembic:** `charges.currency` (`String(3)`, NOT NULL, `server_default='RUB'` + backfill
  существующих в RUB — безопасно на непустой БД, как в TASK-0042); `users.last_currency`
  (`String(3)`, nullable или дефолт `RUB`). Только Alembic; проверить на Postgres.
- **Модель:** `Charge.currency`, `User.last_currency`. Репозитории charges/users — поддержать поле
  (create принимает currency; user.last_currency обновляется/читается). Доступ — через репозитории.
- **Загрузчик справочника:** сервис (напр. `services/currencies.py`) — загрузка `currencies.json`
  один раз (модульный кэш), API: `get_presets()`, `get_default()`, `is_valid_code(code)`,
  `get(code) -> {code,name,symbol?}`, `search(query) -> list` (по code/name, для TASK-0050),
  `format_amount(amount, code) -> "{amount} {symbol|code}"`. Оффлайн, без сетевых вызовов.
- **Отображение:** заменить зашитый «₽» на валюту списания через форматтер:
  - `services/formatters.py` (TASK-0039) — суммы рендерить через `currencies.format_amount(amount, charge.currency)`.
  - `bot/texts.py` — шаблоны сумм (`new_charge_summary`, `my_charges_card`, `my_charges_item`,
    `my_charges_button`, карточка/напоминание) перевести на `{amount}` без хардкода «₽» (валюту
    подставляет форматтер) — см. строки с «₽».
  - `bot/handlers/charges_list.py` — заменить инлайн `f"... {c.amount} ₽ ..."` (стр. ~82, ~91) на форматтер.
  - Проверить тексты напоминаний (sweep/reminders) — там тоже сумма.

## Критерии приёмки (проверяемые)
- [ ] Миграция: `charges.currency` (NOT NULL, дефолт RUB, backfill) + `users.last_currency`;
      `alembic upgrade head`, `alembic check` пусто, round-trip; smoke на Postgres зелёный.
- [ ] Везде, где раньше было «₽», теперь валюта списания (RUB по умолчанию для старых записей);
      зашитого «₽» в `texts.py`/`handlers` не осталось (grep чисто).
- [ ] Загрузчик справочника: 153 валюты, `is_valid_code`/`get`/`search`/`format_amount` покрыты unit-тестами;
      оффлайн (без сети). Символ для пресетов, код для прочих.
- [ ] Хотя бы один тест форматтера суммы — через реальный `currencies.format_amount` (анти-дрейф).
- [ ] Весь CI начисто зелёный.

## Ожидаемые артефакты
- Миграция, `db/models.py`, `repositories/{charges,users}.py`, `services/currencies.py`,
  `services/formatters.py`, `bot/texts.py`, `bot/handlers/charges_list.py`, тесты.

## Ограничения / заметки
- Конвертацию валют НЕ делаем (вне scope). Валюта — атрибут суммы.
- Миграцию проверять на реальном Postgres (анти-дрейф). Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Нет. (Парная — TASK-0050.)
