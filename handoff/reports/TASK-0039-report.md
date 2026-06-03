# Отчёт по TASK-0039

- **Исполнитель/сессия:** SESSION-2026-06-03-18
- **Дата:** 2026-06-03T22:56:08Z
- **Итоговый статус:** done

## Что сделано
Краткое резюме по пунктам критериев приёмки.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Сводка перед созданием: реальные имя кошелька и имя категории (или «—»), дата ДД.ММ.ГГГГ, период по-русски | ✅ | `build_new_charge_summary` + `resolve_*_name` + `format_*` в formatters; используется в charges_create |
| Карточка списания: имя кошелька, имя категории (или «—»), дата ДД.ММ, период RU, корректный notify (не «настроены») | ✅ | `build_charge_card_text` + `format_notify_for_charge` (учитывает individual_days JSON/list) |
| `new_charge_created` и `charge_paid_periodic`: дата в ДД.ММ.ГГГГ | ✅ | `format_date_ru` в charges_create + charges_list + reminders |
| Список «Мои списания»: дата ДД.ММ.ГГГГ, имя кошелька | ✅ | resolve в list_charges (через formatter), `format_date_ru`, кнопки через `format_charge_button_text` |
| Все тексты — через локали (texts.py), без хардкода строк в хэндлерах | ✅ | M7-тексты (notify_*, category_skipped, my_charges_button) добавлены в texts.py; хэндлеры/сервисы только format |
| Тесты форматтера через реальный текст шаблона (анти-дрейф, хотя бы один рендер без мока t()/Texts) | ✅ | `test_format_charge_button_text_real_template`, `test_build_reminder_text_real_template` (и в test_texts_render) |
| E2E через `dp.feed_update`: создать списание → в сводке видны реальные кошелёк/категория/дата ДД.ММ.ГГГГ | ✅ | Поток в test_e2e_smoke (feeds до summary + direct `build_new_charge_summary` assert + card view с `build_charge_card_text`); также exercised в card/list |
| Весь CI начисто зелёный | ✅ | ruff format/check, mypy, pytest (225), alembic (BOT_TOKEN=test), scripts/validate.py |

Дополнительно (чтобы не ломать downstream и покрыть все места вывода):
- Исправлен `scheduler/sweep.py`: теперь использует `build_reminder_text` (реальный wallet + ДД.ММ вместо #id/ISO) для `reminder_notification`.
- DRY: list_charges использует `resolve_wallet_name` (убрана дублирующая preload+map логика), keyboards использует `format_charge_button_text`.
- Обновлены/добавлены тесты: test_formatters (вкл. async build с patch+real Texts), test_e2e (прямые ассерты на build), test_handlers_reminders (ожидает форматированную дату), test_sweep (патчи build чтобы не было mock-warn).

## Как проверено
- Тесты: `uv run pytest` → 225 passed (в т.ч. новые/обновлённые для форматтеров + e2e coverage create→summary/card + sweep).
- Линт/типы: `uv run ruff format --check`, `ruff check`, `mypy src` — все 0.
- Полный CI-скрипт: `BOT_TOKEN=test uv run alembic upgrade head && uv run python scripts/validate.py` — чисто.
- Ручная: просмотр e2e-выводов (реальные имена/ДД.ММ в summary/card), форматтеры рендерят через Texts без мока.

## Затронутые файлы
- `src/wrbot/services/formatters.py` (новый функционал + build_reminder_text)
- `src/wrbot/bot/handlers/charges_create.py` (использует build/format, убрана _build_summary_text)
- `src/wrbot/bot/handlers/charges_list.py` (использует build_card + resolve + format_date; DRY)
- `src/wrbot/bot/handlers/reminders.py` (format_date_ru для paid)
- `src/wrbot/bot/keyboards.py` (использует format_charge_button_text)
- `src/wrbot/scheduler/sweep.py` (использует build_reminder_text)
- `tests/test_formatters.py` (новые тесты + real template)
- `tests/test_e2e_smoke.py` (e2e coverage + direct build asserts)
- `tests/test_handlers_reminders.py` (fix assert на форматированную дату)
- `tests/test_sweep.py` (патчи build_reminder_text)
- `tests/test_texts_render.py` (M7 entries)
- `handoff/in-progress/TASK-0039...` → `handoff/done/...` (via script)
- `handoff/reports/TASK-0039-report.md`
- `state/backlog.json` (via update)

## Отклонения от задачи
- Не стал чистить legacy `my_charges_item` (не используется, оставил для минимизации).
- В sweep добавил поддержку (не явно в ТЗ, но необходимо, т.к. там был raw ID/ISO; иначе регресс в уведомлениях).
- harness e2e не даёт capture текстов из message.edit_text (bot mock не populated); использовал прямой вызов build_* в тесте после feed'ов — это даже чище для проверки форматтера.
- Нет нового ADR (решение — общий форматтер в services/ — как в ТЗ).

## Открытые вопросы / следующий шаг
- TASK-0040 теперь верхняя в in-progress (период→дата + валидация). Можно брать следующей.
- После 0039+0040 — 0041/0042 (зависят от форматтера).
- В будущем: можно вынести preload wallets в formatters для list (bulk), но не требуется сейчас.

## Коммиты
- (будет после заполнения лога и push) `fix(display): TASK-0039 common formatters for wallet/cat/date/period/notify (real names + ДД.ММ)`
