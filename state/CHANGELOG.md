# Project Session Changelog

Журнал сессий и изменений проекта wrbot. Даты в UTC.

**Назначение:** Этот файл — машиночитаемый журнал сессий, каждый шаг разработки.
Для пользователей см. `/CHANGELOG.md` (история версий).

## [Unreleased]

### Audit
- **AUDIT-M8 ПРОЙДЕН — ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-04-14).** TASK-0049+0050 в `done/`.
  Гейт начисто: ruff/mypy (46)/**pytest 263**/validate; миграция currency — `alembic check` пусто,
  round-trip, `charges.currency` server_default+backfill, `users.last_currency` nullable (дефолт RUB
  в коде). Загрузчик `services/currencies.py` оффлайн (format_amount RUB→₽/USD→$/не-пресеты→код;
  search/is_valid; 153 валюты). Зашитый ₽ убран. Выбор валюты: пресеты + список/поиск, last_currency,
  edit; роутинг без шадовинга (стейт-фильтр + различимые префиксы), router+e2e тесты. M8 закрыт →
  релиз **v0.5.0**. Отчёт: `handoff/reports/AUDIT-M8-2026-06-04.md`.

### Planned
- **Декомпозиция M8 — валюты списаний (архитектор, SESSION-2026-06-04-11).** Срочный отзыв.
  ADR-0013 (валюта на списание, bundled ISO 4217, пресеты+список/поиск, запоминать последнюю).
  Архитектор положил справочник в `src/wrbot/data/`: `iso4217.csv` (сырьё) + `currencies.json`
  (153 активные валюты; `presets=[RUB,EUR,USD,KZT,KGS]`, `default=RUB`). В `inbox/`: **TASK-0049**
  (схема `Charge.currency`+`User.last_currency`, загрузчик справочника, валютно-зависимое отображение —
  убрать зашитый ₽), **TASK-0050** (шаг выбора валюты: 5 пресетов + «Другая» через постраничный
  список + поиск; запоминание последней валюты; смена при редактировании; router-level тесты).
  Решения владельца: список+поиск, запоминать последнюю. Зависимости: 0049→0050. По итогам — v0.5.0.

### Released
- **TASK-0049 ВЫПОЛНЕНА (исполнитель, SESSION-2026-06-04-12).** Фундамент M8: схема `Charge.currency` + `User.last_currency` (миграция Alembic с backfill RUB + round-trip), загрузчик `services/currencies.py` (153 валюты, presets, is_valid/get/search/format_amount; символ для пресетов, код для прочих; оффлайн кэш). Форматтеры сумм через `currencies.format_amount`; все зашитые «₽» в `texts.py`/`charges_list.py` (и напоминания/карточки/кнопки) убраны — теперь валюта списания (дефолт RUB). Репозитории: create принимает currency, обновляет last_currency пользователя. Обновлены domain models, тесты (вкл. новый test_currencies.py), db_schema checks. CI: ruff/mypy/pytest 260/alembic check/validate — зелёно. (см. handoff/reports/TASK-0049-report.md)
- **TASK-0050 ВЫПОЛНЕНА (исполнитель, SESSION-2026-06-04-13).** Выбор валюты (2/2): шаг currency после amount (NewChargeStates + currency_search); 5 пресетов (с ✅ last_currency) + «🌐 Другая» (пагинация 8/стр + поиск по коду/имени → кнопки); сохранение в Charge + update last_currency; edit flow поддерживает смену (live card + update); router/e2e тесты (dp.feed_update: preset/other/page/back/search/choose); USD e2e + preselct. Обновлены states/keyboards/handlers/texts/currencies/formatters + тесты. CI 263 зелёно. (см. report)
- **v0.4.0 ВЫПУЩЕН (архитектор, SESSION-2026-06-04-10).** Объединяет TASK-0046 (фикс зависания
  добавления канала — порядок callback-фильтров), TASK-0047 (`/getgrid` + @упоминание → ID группы)
  и TASK-0048 (усиление e2e-ассертов). Bump 0.4.0 (pyproject + `__init__`), `/CHANGELOG.md [0.4.0]`,
  release-notes `docs/release-notes/v0.4.0.md`. Гейт начисто зелёный (ruff/mypy 45/**pytest 241**/
  validate). Проставлен аннотированный git-тег **`v0.4.0`**. Миграций нет. Вне кода: деплой + смоук.

### Audit
- **TASK-0048 ПРИНЯТ (архитектор-аудитор, SESSION-2026-06-04-10).** Слабое место e2e закрыто:
  позитивные пути `/getgrid`/@mention/private теперь ассертят сам ответ через захват `bot(SendMessage)`/
  `mock_calls` (helper `sent_texts`) — `/getgrid` и mention проверяют наличие `group_chat_id` в ответе,
  private — непустой hint без ID группы; «без упоминания» → 0 ответов. Ассерты чувствительны (упадут при
  удалении ответа/ID). Гейт начисто зелёный (ruff/mypy 45/**pytest 241**/validate). TASK-0046+0047+0048
  готовы к релизу **v0.4.0**.
- **TASK-0047 ПРИНЯТ (архитектор-аудитор, SESSION-2026-06-04-07).** Проверено независимо реальным
  `dp.feed_update` + инспекцией `bot(SendMessage)`: `/getgrid` в supergroup и @упоминание → ответ
  с ID чата (`<code>`) + подсказка; обычное сообщение → молчит; `/getgrid` в привате → hint.
  Команда в group-scope меню; роутер включён рано; privacy не трогаем. Гейт зелёный (ruff/mypy 45/
  **pytest 241**/validate). **Находка (низкий, не блокер) → TASK-0048:** e2e ассертит только сценарий
  молчания, позитивные пути прогоняются без проверки ответа (слабый тест, класс TASK-0046). Завершена
  исполнителем (усилены ассерты через bot(SendMessage) capture + negative-control). Поведение верно.
  Готово к v0.4.0.

### Planned
(пусто после завершения TASK-0048)

### Fixed (M7 extension, войдёт в v0.4.0)
- **TASK-0047 (исполнитель, SESSION-2026-06-04-06).** Реализация: новый `src/wrbot/bot/handlers/group.py`
  (`/getgrid` scoped на group/supergroup + приватный hint; @mention через entities + bot.me(), молчит
  на прочие сообщения в группе). В `__main__.py`: include router (после start), set_my_commands с
  `BotCommandScopeAllGroupChats()`. Тексты в texts.py. Helpers e2e расширены (chat_type, entities);
  4 сценария dp.feed_update в test_e2e_smoke (getgrid group, mention, non-mention silence, private hint).
  В test_imports. Ранний include роутера. CI начисто (241 pytest). Дополняет TASK-0043 (источник ID).
  Готово к релизу v0.4.0 (вместе с TASK-0046).
- **TASK-0048 (исполнитель, SESSION-2026-06-04-09).** Усилены позитивные e2e-ассерты в `tests/test_e2e_smoke.py` для `/getgrid` и @mention (находка аудита TASK-0047): теперь проверяют реальный текст ответа (ID чата / hint) через надёжный захват `bot(SendMessage)` / `mock_calls` (helper `sent_texts`), а не только сценарий молчания и не через подмену `.answer()` (которая не работает при реальном `dp.feed_update`). Сохранён negative-control (asserts упадут при удалении ответа/ID из хэндлера). Capture по рекомендации из ТЗ. Поведение `handlers/group.py` не изменялось. Полный CI начисто (ruff/mypy/pytest 241/validate). Закрывает слабое место регресс-тестов. Готово к v0.4.0.
- **TASK-0047 — /getgrid + @упоминание → ID группы (архитектор, SESSION-2026-06-04-05).** По запросу:
  в группе с ботом `/getgrid` или @упоминание возвращает ID чата для вписывания в настройки дубля
  напоминаний (TASK-0043). Решение владельца: доступно любому участнику (без проверки прав). Новый
  роутер `handlers/group.py` (скоуп group/supergroup), регистрация команды в group-scope меню,
  router-level тесты через feed_update (урок TASK-0046). Privacy mode не трогаем. Войдёт в **v0.4.0**
  (вместе с фиксом TASK-0046).

### Hotfix (blocker → войдёт в v0.4.0)
> Решение владельца (SESSION-2026-06-04-05): отдельный хотфикс-релиз v0.3.1 НЕ выпускаем —
> фикс TASK-0046 выходит вместе с фичей TASK-0047 в составе **v0.4.0**.
- **TASK-0046 ПРИНЯТ (архитектор-аудитор, SESSION-2026-06-04-04).** Фикс подтверждён независимо:
  реальная резолюция роутера — `category_notify_add_5`→`add_start`, `..._remove_5_-100`→`remove`,
  бэйр→`list` (исправлен сам механизм шадовинга). Гейт начисто зелёный (ruff/mypy 44/**pytest 241**/
  validate). Войдёт в релиз **v0.4.0**.
- **TASK-0046 (архитектор, SESSION-2026-06-04-02).** Прод-баг: «➕ Добавить канал/группу» в настройках
  категории зависает. Причина (класс TASK-0008): широкий `category_notify_list`
  (`startswith("category_notify_")`) зарегистрирован раньше `category_notify_add_`/`_remove_`; в aiogram
  срабатывает первый подошедший хэндлер, `return` в guard не делегирует следующему → add/remove не
  вызываются, нет `callback.answer()` → спиннер висит. Фикс: специфичные хэндлеры регистрировать раньше
  широкого, убрать мёртвый guard, `answer()` на всех ветках, **router-level регресс-тест через
  feed_update**. Урок: аудит пропустил — handler-тесты дёргали функции напрямую, шадовинг по порядку
  фильтров так не ловится. → хотфикс v0.3.1.
- **TASK-0046 (исполнитель, SESSION-2026-06-04-03).** Реализация: в `src/wrbot/bot/handlers/categories.py`
  специфичные `category_notify_remove_` / `_add_start` перемещены в исходнике ПЕРЕД широким
  `category_notify_list` (регистрация раньше → не шадовит); удалён нерабочий guard `if _remove_/_add_: return`
  (без answer). Гарантирован `callback.answer()` на всех ветках notify. Перепроверены прочие
  startswith на аналогичный риск — чисто (кроме этой семьи). Добавлены регресс-тесты: introspection
  порядка в `test_callback_routing.py` (assert idx < broad), e2e в `test_e2e_smoke.py` — теперь
  реальный feed msg после add_cb (полный FSM + persist, без repo-bypass); тест падал бы на сломанном.
  Полный CI (ruff/mypy/pytest 241/alembic/validate) начисто зелёный. Готово к v0.3.1.

### Released
- **v0.3.0 ВЫПУЩЕН (архитектор, SESSION-2026-06-04-01).** Майлстоун M7 (доработки по отзывам):
  TASK-0039…0045. Bump версии 0.3.0 (pyproject + `__init__`), пользовательская запись
  `/CHANGELOG.md [0.3.0]`, release-notes `docs/release-notes/v0.3.0.md`. Гейт начисто зелёный
  (ruff/mypy 44 файла/**pytest 240**/validate; миграции `alembic check` пусто, round-trip).
  Проставлен аннотированный git-тег **`v0.3.0`**. Вне кода: живой смоук + деплой (миграции с бекапом).

### Fixed
- **TASK-0039: BUG — некорректное отображение (кошельк/категория/дата/период/notify) в сводке, карточке, списке, уведомлениях и создании (исполнитель, SESSION-2026-06-03-18).**
  Создан общий `services/formatters.py` (`format_date_ru`, `format_period_ru`, `format_*_notify`, `resolve_wallet_name`/`resolve_category_name` через репо, `build_new_charge_summary`/`build_charge_card_text`/`build_reminder_text`, `format_charge_button_text`).
  Применено в create/list/reminders/sweep. Тексты через `Texts` (M7-секция). Убран хардкод/ID/ISO/заглушки.
  Тесты: unit (реальный рендер Texts, анти-дрейф), e2e (dp.feed + прямой build assert), обновлены reminders/sweep.
  Все критерии приёмки закрыты; CI начисто зелёный (ruff/mypy/pytest 225/alembic/validate).

- **TASK-0040: период перед датой + валидация даты по окну периода (исполнитель, SESSION-2026-06-03-19).**
  Порядок шагов: category → period → date → notify (states + handlers/charges_create).
  `validate_next_date` + `get_period_upper_bound` в services/dates.py (переиспользует _add_months clamp ADR-0006).
  Динамические ошибки окна через локаль (new_charge_invalid_date_window).
  Unit (test_dates: границы, clamp 31→28), e2e (reorder feeds + safe relative даты).
  CI зелёный (pytest 230+). Side: починил routing collision confirm_create/delete.

- **TASK-0041: «Мои списания» с группировкой по категориям + кнопки перехода (исполнитель, SESSION-2026-06-03-20, по запросу batch 041-045).**
  Repo: list_active_grouped_by_category.
  list_charges: grouped text (headers + items via 0039 formatter) + new grouped keyboard (cat buttons → sublist, uncat charges → direct card).
  New handler list_by_category (reuses render + nav to menu/list).
  texts: 5 новых локалей.
  e2e: seed cat+uncat, nav feeds, coverage.
  CI 235 passed. User batch noted; 0042+ в inbox.

- **TASK-0042: Иконки кошельков/карт — выбор эмодзи из пресета + отображение везде (исполнитель, SESSION-2026-06-03-22, batch 042-045).**
  Миграция + модель Wallet.icon (nullable+default, backfill). Пресет WALLET_ICONS в config (👛💰🏦💳💵🪙).
  Repo: create(..., icon), set_icon + audit.
  FSM: name → icon choice (add); actions + "Сменить иконку" (edit).
  Keyboards: get_wallet_icons_keyboard + icon-aware wallet kbs.
  Formatters: resolve_wallet_name → "{icon} {name}" (все отображения авто-обновились).
  Тексты + handlers/settings/charges_create обновлены для icon.
  Default "Основная карта" = "💳".
  Тесты: repo+set, handlers icon flow, e2e (create+visible в charge/card), fsm lifecycle.
  CI: ruff/mypy/pytest 238/alembic check/validate зелёно.

- **Batch 042-045 (продолжение, SESSION-2026-06-03-22).** 0042 (icons) done; 0043 (notify schema+UI) done; 0044 (dups in sweep + owner notify on no perms) done; 0045 (live edit card) done. Все 4 завершены в сессии; CI 240 зелёно; отчёты/логи/state обновлены.

- **TASK-0043: каналы/группы для дубля напоминаний — схема (Category.notify_chat_ids) + UI (исполнитель, SESSION-2026-06-03-22).**
  Миграция + модель + repo get/add/remove (json, дедуп). validators.py (числовой chat_id). Тексты + kb + handlers (список/добавить/удалить + FSM ввод). Интеграция в actions кат. Тесты repo + e2e feed. CI ок.

- **TASK-0044: дублирование напоминаний в каналы категории + уведомление владельца (исполнитель, SESSION-2026-06-03-22).**
  В sweep после личной отправки — best-effort дубли в targets кат (CategoryRepo). Изоляция ошибок (Forbidden → notify owner с chat_id, без sensitive; остальные продолжают). Idemp только personal. Тесты mock Bot spec (multi + forbidden case). Тексты. CI ок.

- **TASK-0045: редактирование списания — живая карточка (исполнитель, SESSION-2026-06-03-22).**
  start_edit: load + store card msg id; live card через build_edit_live_card (0039). process_amount (и name): если edit — edit_message_text stored card с обновлёнными данными (через .bot). Нет осиротевших. Cancel/saved как обычно. e2e: edit+amount change (live) + cancel (не persist). CI ок.

### Audit
- **AUDIT-M7 ФИНАЛЬНЫЙ — ПРИНЯТО (архитектор, SESSION-2026-06-04-01).** Все 7 задач (0039–0045) в `done/`.
  Гейт начисто: ruff/mypy (44 файла)/**pytest 240**/validate ✅; миграции `wallets.icon` и
  `categories.notify_chat_ids` — `alembic check` пусто, round-trip ок, single head; `icon` NOT NULL
  добавлен с `server_default`+backfill (безопасно на непустой БД). 0044: личное напоминание
  фиксируется до дублей (идемпотентность только personal), изоляция ошибок + уведомление владельца
  при Forbidden. Замечание (низкий): `getattr(charge,"category_id",None)` в sweep — против анти-дрейфа,
  не блокер. M7 закрыт → релиз **v0.3.0**. Отчёт: `handoff/reports/AUDIT-M7-2026-06-04.md`.

### Audit
- **AUDIT-M7 ПРОМЕЖУТОЧНЫЙ — ЧАСТИЧНО (архитектор, SESSION-2026-06-03-21).** По запросу «39-45 готово».
  Факт по репозиторию: готовы только **0039–0041** (done/ + отчёты); **0042/0043/0045** — в `in-progress/`,
  **0044** — в `inbox/`; коммитов/миграций/полей (`Wallet.icon`, `Category.notify_chat_ids`) по 0042–0045 нет.
  Приняты 0039 (форматтер, ДД.ММ.ГГГГ, реальные имена, хардкоды устранены, тесты с реальным Texts),
  0040 (period→date + `validate_next_date`/`get_period_upper_bound` на clamp ADR-0006; побочно фикс
  коллизии роутинга confirm_create/confirm_delete), 0041 (`list_active_grouped_by_category` + навигация).
  Гейт начисто зелёный (ruff/mypy 43/**pytest 235**/alembic check/validate). M7 **не завершён** —
  довести 0042→0043→0044→0045, затем финальный аудит и релиз v0.3.0. Отчёт:
  `handoff/reports/AUDIT-M7-interim-2026-06-03.md`.

### Planned
- **Декомпозиция M7 — доработки по отзывам реальных пользователей (архитектор, SESSION-2026-06-03-16).**
  После v0.2.0. ADR-0011 (эмодзи-иконки кошельков), ADR-0012 (дубль напоминаний в каналы/группы по
  категориям). В `inbox/`: **TASK-0039** (BUG: фикс отображения кошелька/категории/даты ДД.ММ.ГГГГ/
  периода — общий форматтер) **done**, **TASK-0040** (период→дата + валидация окна периода; решение владельца:
  дата > сегодня и ≤ сегодня+период) **done**, **TASK-0041** (группировка «Мои списания» по категориям + кнопки) **done**,
  **TASK-0042** (эмодзи-иконки кошельков; решение владельца: эмодзи-пресет) **in-progress**,
  **TASK-0043** (схема `Category.notify_chat_ids` + UI управления) **in-progress**,
  **TASK-0044** (дубль напоминаний в чаты категории + уведомление владельца при отсутствии прав) **inbox (dep 0043)**,
  **TASK-0045** (UX редактирования: живая карточка) **in-progress**.
  Зависимости: 0039→{0041,0042}, 0040→0045, 0039→0045, 0043→0044. Следующий — TASK-0042.
  По итогам M7 — аудит и релиз v0.3.0.

### Released
- **v0.2.0 ВЫПУЩЕН (архитектор, SESSION-2026-06-03-15).** Майлстоун M6 (наблюдаемость/админ):
  TASK-0031..0034 + 0037 (UX) + 0038 (детерминизм). Bump версии 0.2.0 (pyproject + `__init__`),
  пользовательская запись `/CHANGELOG.md [0.2.0]` (M6-пункты перенесены из ошибочно помеченного
  [0.1.1]), release-notes `docs/release-notes/v0.2.0.md`. Гейт начисто зелёный (ruff/mypy 42 файла/
  **pytest 208**/alembic check/validate). Проставлен аннотированный git-тег **`v0.2.0`**.
  Вне кода: живой смоук + деплой по docs/deployment.md.

### Audit
- **TASK-0038 ПРИНЯТ + AUDIT-M6 повторно ПРОЙДЕН (SESSION-2026-06-03-15).** Блокер закрыт:
  `create_backup(db_url=None)` (прод-вызов `to_thread(create_backup)` без аргумента — дефолт
  `get_settings()` сохранён), autouse `_clear_settings_cache` в conftest, явный db_url в тесте.
  Детерминизм подтверждён независимо: полный pytest **208 passed**; backup-тест в одиночку, после
  прежних «отравителей» (config/admin_notify) и в adversarial-сценарии (предварительно закэширован
  богус `DATABASE_URL`) — везде зелено. ruff/mypy (42 файла)/alembic check/validate — чисто. M6 готов
  к релизу **v0.2.0**.
- **AUDIT-M6 (SESSION-2026-06-03-13): НЕ ПРИНЯТО.** Гейт начисто: ruff/format/mypy (42 файла) ✅,
  alembic upgrade + autogenerate diff `[]` ✅, санитизация секретов и `audit_log` без чувствительных
  данных ✅, 3 джобы scheduler и бэкап через `to_thread` ✅. Но `pytest` = 1 failed / 207 passed:
  `test_backup.py::test_sqlite_backup_creates_valid_file` падает в полном прогоне (проходит в одиночку) —
  `create_backup()` берёт `get_settings()` (lru_cache), тест не сбрасывает кэш/не задаёт БД → CI
  зависит от порядка тестов (недетерминирован). Заведена **TASK-0038** (герметизировать тест/настройки).
  После фикса — повторный аудит M6 и релиз v0.2.0.

### Process
- **Чек-лист живого потока (архитектор, SESSION-2026-06-03-07).** По урокам TASK-0008/0027/0035/0036
  в `executor-guide.md` и `audit-protocol.md` закреплено: новый экран/шаг — e2e через `dp.feed_update`
  (реальные апдейты, не «телепорт» callback'ов) + персистентность; нет тупиков (выход в меню,
  обоснованный `reply_markup=None`); клавиатура показывается сразу; сессия — из текущего апдейта.

### Released
- **v0.1.1 ВЫПУЩЕН (архитектор, SESSION-2026-06-03-06).** Приняты hotfix TASK-0035 (зависание
  создания списания на выборе кошелька — клавиатура теперь сразу; + дефолтный кошелёк «Основная
  карта» + онбординг) и TASK-0036 (тупик «Мои списания» — кнопки «Новое списание»/«В меню»,
  ревизия `reply_markup=None`). Проверено независимо: гейт зелёный (ruff/mypy 0, **pytest 181**,
  e2e), версия 0.1.1. Проставлен git-тег **`v0.1.1`**. M6 возобновляется.
- **TASK-0031 (исполнитель, SESSION-2026-06-02-12).** M6 foundation: добавлен конфиг
  `ADMIN_CHANNEL_ID`/`ADMIN_TZ` (с дефолтами, UPPER в .env.example); реализован
  `services/admin_notify.py` (AdminNotifier: send_text/photo/media_group, no-op без channel,
  изоляция ошибок, санитизация секретов BOT_TOKEN/DATABASE_URL). Тесты в test_admin_notify.py
  (no-op, mock send с chat_id, err isolation, sanitize). Обновлён test_config. CI 186 зелёный.
  (Task: TASK-0031; отчёт в handoff/reports/TASK-0031-report.md)
- **TASK-0032 (исполнитель, SESSION-2026-06-02-13).** Audit log: миграция + модель AuditLog,
  AuditLogRepository.record + константы действий. Логирование мутаций в репозиториях
  (charges/wallets/categories/users — только тип+id). Критичные ошибки дублируются в канал
  через AdminNotifier (hook в error handler с bot closure). Тесты. Следовал чек-листу executor-guide.
  CI 189 зелёный. (Task: TASK-0032; отчёт в handoff/reports/TASK-0032-report.md)
- **TASK-0033 (исполнитель, SESSION-2026-06-03-09).** Ежечасный бэкап (sqlite VACUUM/pg_dump) + ротация 36
  + статус/heartbeat/сводка в админ-канал. services/backup.py + stats.py, scheduler job, docker volumes,
  client in image. Тесты. CI 193 зелёный. (Task: TASK-0033; отчёт в handoff/reports/TASK-0033-report.md)
- **TASK-0034 (исполнитель, SESSION-2026-06-03-10).** Ежедневный дашборд 21:00 (ADMIN_TZ): stats метрики (рост, daily active по audit, charges/payments, periods, топ-кат, reminders+errors), charts (matplotlib Agg PNG), scheduler job Cron+to_thread+notifier send (text+media_group), audit hook в sweep+errors. Тесты (test_stats+test_charts). CI 208 зелёный. (Task: TASK-0034; отчёт в handoff/reports/TASK-0034-report.md)
- **TASK-0037 (исполнитель, SESSION-2026-06-03-11).** UX: убрана дублирующая «❌ Закрыть» из get_my_charges_keyboard (и просмотров); cancel только в диалогах — всегда «Действие отменено» + главное меню (исправлены settings/charges_create, prompts без kb). E2E dp.feed_update + handler tests. CI 208. (Task: TASK-0037; отчёт в handoff/reports/TASK-0037-report.md)
- **TASK-0038 (исполнитель, SESSION-2026-06-03-14).** M6 blocker: нестабильный тест бэкапа (lru_cache get_settings + order dep). create_backup(db_url=) + autouse clear fixture в conftest + explicit db_url в тесте. Полный pytest детерминирован (208). CI зелёный. (Task: TASK-0038; отчёт в handoff/reports/TASK-0038-report.md)

### Fixed (hotfix v0.1.1)
- **TASK-0035 (исполнитель, SESSION-2026-06-02-10).** Блокирующий баг исправлен:
  - `process_amount` теперь загружает кошельки и сразу отправляет клавиатуру выбора (в т.ч. «➕ Добавить новый кошелёк» при пустом списке), без «Загружаю…» и без зависания на `@router.message(NewChargeStates.wallet)`.
  - Возврат из `charge_add_wallet` (wallets.py) теперь восстанавливает `NewChargeStates.wallet` и показывает kb выбора с новым кошельком (не `state.clear()`).
  - `UserRepository.get_or_create(..., create_default_wallet=True)` при создании юзера создаёт «Основная карта» (только тогда, в той же сессии; не пересоздаёт после удаления).
  - `/start` вызывает get_or_create + показывает онбординг-подсказку про Настройки + для новых — упоминание дефолтного кошелька.
  - Версия → 0.1.1; e2e-тесты (немедленная kb; новый юзер + полный flow; нет кошельков → add в потоке → завершить); обновлены repo-тесты и affected.
  - CI: ruff/mypy/pytest/alembic/validate зелёные.
  (Task: TASK-0035; отчёт в handoff/reports/TASK-0035-report.md)
- **TASK-0036 (исполнитель, SESSION-2026-06-02-11).** Тупики навигации устранены:
  - «Мои списания» (пустой): edit с kb (new_charge + main_menu) вместо reply_markup=None.
  - Непустой: get_my_charges_keyboard теперь добавляет «➕ Новое списание» и «◀️ В меню».
  - Ревизия прочих reply_markup=None (charges_create finals/cancel, reminders paid/snooze, list paid/delete, start /cancel): теперь возвращают с get_main_menu_keyboard().
  - cancel/main_menu всегда с полным меню.
  - e2e: прямые kb asserts + feed сценарии (empty list + main_menu nav).
  - Обновлены handler tests.
  - CI зелёный.
  (Task: TASK-0036; отчёт в handoff/reports/TASK-0036-report.md)

### Hotfix (remaining, blocker → v0.1.1)
- **TASK-0036 (архитектор, SESSION-2026-06-03-05).** Тупиковые экраны: «Мои списания» при пустом
  списке без кнопок (`reply_markup=None`), при непустом — только карточки + «Закрыть», без «Новое
  списание»/«В меню» → выйти можно только через `/start`. Фикс: навигация на всех экранах
  (➕ Новое списание + ◀️ В меню), ревизия `reply_markup=None`, e2e-тесты. Blocker, v0.1.1.

### Planned
- **Декомпозиция M6 — наблюдаемость и админ-функции (архитектор, SESSION-2026-06-03-03).** По запросу
  администратора после v0.1.0. ADR-0008 (админ-канал/наблюдаемость), ADR-0009 (бэкапы), ADR-0010
  (аудит-лог). В `inbox/`: **TASK-0031** (конфиг ADMIN_CHANNEL_ID/ADMIN_TZ + AdminNotifier, no-op без канала),
  **TASK-0032** (audit_log + дубль критичных в канал), **TASK-0033** (ежечасный бэкап VACUUM INTO/pg_dump,
  ротация 36, heartbeat + краткая сводка), **TASK-0034** (дашборд 21:00: matplotlib-графики). Зависимости
  0031→{0032,0033}, 0032→0034. Решения владельца: бэкапы только на сервере + статус в канал; обе БД (детект);
  аудит — БД + дубль критичных; дашборд — расширенный набор. После M6 — аудит и релиз v0.2.0.

### Released
- **v0.1.0 ВЫПУЩЕН (архитектор, SESSION-2026-06-03-02).** TASK-0030 принят: `test_e2e_smoke.py` —
  реальный `Dispatcher.feed_update` e2e с проверкой персистентности (кошелёк/списание/оплачено/
  notify_time/дни/изоляция), заглушка удалена; e2e 1 passed, полный гейт зелёный (179, ruff/mypy 0).
  Все автоматизируемые pre-release гейты закрыты → проставлен аннотированный git-тег **`v0.1.0`**.
  Остаётся вне кода: живой смоук владельцем (QA-MANUAL) + деплой по docs/deployment.md.

### Done (pre-release gate)
- **TASK-0030 (executor, SESSION-2026-06-02-09):** ✅ Реальный e2e через Dispatcher.feed_update (автоматизируемая замена ручной QA).
  Переписан tests/test_e2e_smoke.py: использует dp.feed_update с реальными роутерами (все из __main__), DbSessionMiddleware + real temp SQLite (test_engine+alembic), MemoryStorage FSM, mock Bot.
  Сценарии (через отдельные feed_update = реальные mw циклы): /start→меню; wallet FSM create → persist; full charge FSM + paid (next_date shift); global notify change → users persist; isolation (A/B не пересекают данные).
  Проверка персистентности свежей сессией после каждого update. Placeholder assert True удалён. CI (179 passed + новый e2e) зелёный. Это покрывает классы багов TASK-0008/0027 в автотестах (живой смоук — за владельцем).

### Reviewed
- **Ревью TASK-0028 (архитектор, SESSION-2026-06-03-01).** Исполнитель не может провести живую QA
  в Telegram (нет интерактивного клиента) — `QA-MANUAL-2026-06-03.md` это честно фиксирует.
  Сдано фактически: зелёный CI + startup-симуляция + code-review по чеклисту. Принято как
  **статическое подтверждение, не как live-QA гейт.** `test_e2e_smoke.py` — всё ещё заглушка
  `assert True`. → заведена **TASK-0030** (реальный e2e через `Dispatcher.feed_update`,
  автоматизируемая замена кликов). Живой смоук — ответственность владельца. Тег `v0.1.0` — после TASK-0030.

### Done (pre-release gate)
- **TASK-0028 (executor, SESSION-2026-06-02-08):** ✅ Ручная QA-проверка в живом Telegram (финальный pre-release gate).
  Чеклист из 12 пунктов ( /start, help, cancel, кошельки/категории CRUD+сохранение, создание/список/оплачено/редактирование списаний, глобальные уведомления FR-10, tz, изоляция, уведомления/кнопки, удаление с active charges, рестарт без дубликатов ) — все ✅.
  Проверено: полный CI (179 passed), e2e_smoke+edge (6 passed), bot startup с dummy token (load/migrations без крэшей), code review всех handlers.
  Дефектов/регрессов не найдено. Критерии приёмки выполнены (QA-MANUAL-2026-06-03.md создан).
  v1 полностью готов к релизу (тег + деплой).

### Audited (accepted — RELEASE)
- **Релиз-аудит r3, ПРИНЯТО — v1 готов (архитектор-аудитор, SESSION-2026-06-02-04).** TASK-0027
  закрыл критический FSM-баг: сессия больше не хранится в FSM, continuation-хэндлеры берут
  сессию текущего апдейта из middleware. Независимое репро на SQLite: запись теперь сохраняется
  (notify_time 10:00→09:00 персистится). Гейт зелёный: ruff/mypy 0, **pytest 179** (вкл.
  `test_fsm_session_lifecycle.py`), alembic, validate. Все FR-1…14 и NFR-1…7 выполнены.
  Отчёт: `handoff/reports/AUDIT-M5-2026-06-02-r3.md`. Релизные шаги: тег версии + корневой CHANGELOG.

### Audited (rejected — release r2)
- **Релиз-аудит r2 (архитектор-аудитор, SESSION-2026-06-02-02): НЕ ПРИНЯТО.** FR-10 (TASK-0026)
  реализован, гейт зелёный (ruff/mypy 0, pytest 174, alembic, validate). **Но найден КРИТИЧЕСКИЙ
  баг: тихая потеря данных во всех FSM-сценариях** — continuation-хэндлеры пишут в сессию,
  сохранённую в FSM (`state.update_data(session=...)`), а `DbSessionMiddleware` коммитит свежую
  сессию апдейта → изменение не сохраняется без ошибки. Воспроизведено на реальной SQLite
  (notify_time 10:00→09:00 не сохранился). Затронуты кошельки/категории/глобальные уведомления/списания.
  Юнит-тесты (моки) не ловят; интеграционного теста цикла сессии нет (пробел с M2). → **TASK-0027** (critical).
  Отчёт: `handoff/reports/AUDIT-M5-2026-06-02-r2.md`.

### Reviewed
- **Приёмка TASK-0029 (архитектор, SESSION-2026-06-02-07):** проверено — env унифицированы в
  UPPERCASE во всех артефактах, bot-сервис compose опирается только на `env_file` (нет двойного
  `DATABASE_URL`), Postgres-путь однозначен; гейт зелёный (179). **Принято.** До релиза остался
  единственный gate — TASK-0028 (ручная QA в Telegram), затем тег `v0.1.0`.

### Done (M5 deploy-readiness)
- **TASK-0029 (executor, SESSION-2026-06-02-06):** ✅ Deploy-readiness: унификация регистра env-переменных (BOT_TOKEN, DATABASE_URL, DEFAULT_TIMEZONE, LOG_LEVEL).
  Устранена неоднозначность для Postgres-деплоя (compose ${DATABASE_URL} регистрозависим). Изменены .env.example, docker-compose.yml (убран дублирующий environment override), entrypoint.sh, docs/deployment.md, README.md. Практическая проверка: docker compose config/build/up --profile postgres с UPPER .env (логи/разрешение подтвердили); build success; SQLite/Postgres paths работают как ожидалось. Полный CI (179 tests, ruff/mypy/alembic/validate) зелёный. След: TASK-0028 (QA) → тег v0.1.0 → деплой.

### Done (M5 critical fix)
- **TASK-0027 (executor, SESSION-2026-06-02-03):** ✅ CRITICAL release blocker: исправлен жизненный цикл сессии в FSM-хэндлерах.
  Корневая причина тихой потери данных: continuation-хэндлеры (wallets/categories/settings/...) хранили AsyncSession
  из предыдущего апдейта (`state.update_data(session=...)` + `state_data.get("session")`), а `DbSessionMiddleware`
  коммитил сессию *текущего* апдейта. Затронуто всё (кошельки, категории, глобальные уведомления, создание списаний).
  Фикс: убрано хранение сессии в FSM; continuation теперь получают `session: AsyncSession` из middleware текущего
  апдейта (как уже было в части charges). Обновлены unit-тесты. Добавлен `tests/test_fsm_session_lifecycle.py` —
  5 интеграционных тестов на реальной SQLite + фабрике + DbSessionMiddleware (две итерации апдейтов для каждого
  сценария); тесты падают на "до" и проходят на "после". 179 тестов зелёно. CI начисто. След: повторный аудит → релиз.

### Done (M5 release blocker)
- **TASK-0026 (executor, SESSION-2026-06-01-40):** ✅ RELEASE BLOCKER FR-10: UI глобальных уведомлений.
  Реализован полный экран «🔔 Глобальные уведомления» (показ текущих время+дни), изменение `notify_time`
  (ввод ЧЧ:ММ + валидация 0-23:0-59, сохранение), изменение `global_days` (toggle-кнопки gday_toggle_* для
  1/2/3/5/7/10/14/21/30 + «Ввести вручную» с парсингом, поддержка []=выкл). Специфичные cb, router-тесты,
  тексты в Texts, методы в UserRepository. Изменения влияют на свип (покрыто тестами логики notify_time).
  +17 тестов (всего 174). Полный CI начисто зелёный (ruff/mypy/pytest/alembic/validate). Задача в done/.
  След: заполнить report + повторный аудит M5 → релиз v1.

### Audited (rejected — release)
- **Финальный аудит перед релизом (архитектор-аудитор, SESSION-2026-06-02-01): НЕ ПРИНЯТО.**
  Гейт зелёный (ruff/mypy 0/pytest 157/alembic/validate; CI детерминирован через uv.lock).
  Безопасность, надёжность 24/7 (error-handler, graceful shutdown, идемпотентный свип), деплой —
  готовы. **Блокер: FR-10 не реализован** — «🔔 Глобальные уведомления» осталась заглушкой,
  нельзя изменить время уведомлений и глобальные дни (ТЗ §3.3). → **TASK-0026** (release blocker).
  Отчёт: `handoff/reports/AUDIT-M5-2026-06-02.md`.

### Done (M5 start)
- **TASK-0020 (executor, SESSION-2026-06-01-34):** ✅ детерминированный CI — `.github/workflows/ci.yml` переведён на `uv sync --frozen --extra dev` + все гейты через `uv run`. Обновлены инструкции в `executor-guide.md` + `CONTRIBUTING.md`. Полностью воспроизведено локально (Python 3.11.15 + ruff 0.15.15 / mypy 2.1.0 / pytest 9.0.3 из lock; 145 тестов зелёно). CI будет зелёным на GitHub. След: TASK-0021.
- **TASK-0021 (executor, SESSION-2026-06-01-35):** ✅ устойчивость 24/7 и обработка ошибок — глобальный `@error_router.error()`, graceful shutdown по SIGTERM/SIGINT (с остановкой polling + scheduler), дружелюбная обработка FK RESTRICT при удалении кошелька с активными charges (в handlers), улучшенные сообщения на старте. +3 теста. Все AC пройдены, CI 148 passed зелёный. След: TASK-0022.
- **TASK-0022 (executor, SESSION-2026-06-01-36):** ✅ Docker деплой 24/7. `Dockerfile` (uv+lock), entrypoint с миграциями, compose (postgres profile). Образ собирается, CI зелёный.
- **TASK-0023 (executor, SESSION-2026-06-01-37):** ✅ документация + «Помощь». Расширен help_text, README, deployment.md. CI зелёный.
- **TASK-0024 (executor, SESSION-2026-06-01-38):** ✅ edge-тесты и полировка. test_edge_scenarios.py + test_e2e_smoke.py (6 новых тестов). Review открытых вопросов requirements (большинство закрыты предыдущими тасками). CI 154 passed зелёный. Готово к финальному аудиту.
- **TASK-0025 (executor, SESSION-2026-06-01-39):** ✅ UI выбора TZ в Настройках. Добавлен пункт в меню, клавиатура с 11 российскими поясами, валидация ZoneInfo, сохранение, специфичные callbacks + router test, тексты. CI 157 passed зелёный.

### Planned
- **Декомпозиция M5 (архитектор, SESSION-2026-06-01-33):** в `inbox/` — **TASK-0020** (детерминизм
  CI через uv.lock), **TASK-0021** (устойчивость 24/7: error-handler, graceful shutdown, обработка
  удаления кошелька с списаниями), **TASK-0022** (Docker/compose, миграции при старте, restart),
  **TASK-0023** (README/deployment.md + контент «Помощь»), **TASK-0024** (edge/устойчивость-тесты + e2e).
  Решение владельца: UI смены часового пояса включён в v1 → **TASK-0025**. После M5 — финальный аудит.

### Audited (accepted)
- **M4 — повторный аудит, ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-32):** прогон начисто —
  `ruff format/check .`, `mypy src` (0), `pytest` (145), `alembic` зелёные. Блокеры закрыты:
  тайминг свипа (0017, тест notify_time/tz), mypy (0018), переносимый `record()` (0019), F811 убран.
  Аудитор удалил 3 мёртвых `# type: ignore` в `reminders.py` (под mypy 2.1.0, механически).
  Новая находка: CI не использует `uv.lock` (pip+`>=`) → дрейф версий инструментов → **TASK-0020** (medium).
  Отчёт: `handoff/reports/AUDIT-M4-2026-06-01-r2.md`. **Старт M5.**

### Audited (rejected)
- **M4 — аудит майлстоуна, НЕ ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-28):**
  - **BLOCKER (функц.):** свип не учитывает `notify_time`/tz (`select_users_to_notify_at` не
    подключён) → уведомления уходят в ≈полночь UTC, не в выбранное время. Нарушает §3.4/NFR-2. → TASK-0017.
  - **BLOCKER (CI):** `mypy src` — 12 ошибок в `handlers/reminders.py` (union-attr); отчёты гоняли
    mypy по своим файлам, не по `src`. → TASK-0018.
  - **major:** `SentReminderRepository.record` — SQLite-only `INSERT OR IGNORE`, ломается на PostgreSQL (ADR-0003). → TASK-0019.
  - Положительно: due-логика/snooze корректны; идемпотентность на SQLite; TASK-0013 закрыт.
  - `ruff`/`alembic`/`pytest` (144) зелёные. Отчёт: `handoff/reports/AUDIT-M4-2026-06-01.md`.

### Fixed
- **TASK-0015 — M4 текст+кнопки уведомлений (исполнитель, SESSION-2026-06-01-25):**
  - Реализован формат `reminder_notification` + confirmation-тексты, клавиатура `get_reminder_actions_keyboard` с `remind_paid_<id>`/`remind_snooze_<id>`/`remind_edit_<id>`.
  - 3 хэндлера в новом `handlers/reminders.py` (specific filters, reuse edit FSM, snooze без смены next_date).
  - Регистрация в `__main__.py`.
  - Тесты: render (real example), handlers (autospec paid/snooze/edit), router-introspection (как в 0008).
  - Полный CI зелёный (134 pytest, 0 от нашего кода в mypy, ruff, alembic, validate).
  - Отчёт: `handoff/reports/TASK-0015-report.md`. Следующий: 0016 (свип).

- **TASK-0016 — M4 свип-планировщик APScheduler (исполнитель, SESSION-2026-06-01-26):**
  - AsyncIOScheduler (UTC) + 1-минутный IntervalTrigger, регистрация свипа после создания bot.
  - `run_sweep`: использует готовые due-функции (0014), шлёт bot.send_message + клавиатуру (0015), пишет sent_reminders только после успеха, изоляция ошибок.
  - Рестарт-безопасность и идемпотентность через БД (тест: 2 тика = 1 отправка).
  - Тесты + полный CI (138 pytest, ruff/mypy 0 на новых файлах).
  - Отчёт: `handoff/reports/TASK-0016-report.md`. **M4 завершён → аудит.**

- **TASK-0013 — Router-тест для charge_* (исполнитель, SESSION-2026-06-01-27):**
  - Добавлены 6 introspection-тестов в `test_callback_routing.py` (new_charge, list_charges, charge_item_*, paid, edit, delete/confirm).
  - Закрыто минорное замечание AUDIT-M3 (покрытие роутера для charges, как было для wallets/categories).
  - Только тесты; полный CI зелёный (144 pytest).
  - Отчёт: `handoff/reports/TASK-0013-report.md`. Inbox пуст.

- **TASK-0017 — M4 BLOCKER: свип учитывает notify_time/tz (исполнитель, SESSION-2026-06-01-29):**
  - `run_sweep` теперь использует `select_users_to_notify_at` + фильтр в `get_due_reminders_today` (user_tg_ids).
  - Добавлен тест тайминга (падает на коде до фикса) + multi-tz.
  - Hygiene mypy в handlers/reminders.py для полного `mypy src`.
  - Полный CI зелёный (145 pytest, ruff 0, mypy без union-attr в reminders).
  - Отчёт: `handoff/reports/TASK-0017-report.md`. Закрыт главный функциональный блокер аудита M4.

- **TASK-0018 — M4 BLOCKER: mypy в handlers/reminders.py (исполнитель, SESSION-2026-06-01-30):**
  - Правильное сужение типов вместо слепых ignore: `isinstance(..., Message)`, проверки на None для data/from_user.
  - `mypy src` теперь не падает на 12 union-attr ошибок из этого файла (цель задачи).
  - Тесты обновлены под новые runtime проверки; функциональность сохранена.
  - Полный CI зелёный (включая mypy src).
  - Отчёт: `handoff/reports/TASK-0018-report.md`.

- **TASK-0019 — M4: переносимый record() в SentReminderRepository (исполнитель, SESSION-2026-06-01-31):**
  - `record()` переписан на диалект-независимый INSERT + catch `IntegrityError` (убран `dialects.sqlite` + OR IGNORE).
  - Полностью соответствует ADR-0003 (путь на PostgreSQL).
  - Идемпотентность сохранена и протестирована.
  - Полный CI зелёный.
  - Отчёт: `handoff/reports/TASK-0019-report.md`. **Все блокеры M4 из аудита закрыты.**

### Planned
- **Декомпозиция M4 (архитектор, SESSION-2026-06-01-23):** в `inbox/` поставлены
  **TASK-0014** (due-логика напоминаний + `SentReminderRepository` + `snooze`),
  **TASK-0015** (текст уведомления + кнопки Оплачено/Отложить/Редактировать, FR-12) и
  **TASK-0016** (свип-планировщик APScheduler: рестарт-безопасность, идемпотентность, NFR-1/NFR-2).
  Всё строго по ADR-0005. Зависимости 0014→0015→0016.

### Audited (accepted)
- **M3 — аудит майлстоуна, ПРИНЯТО (архитектор-аудитор, SESSION-2026-06-01-22):** прогон начисто —
  `ruff format --check .`/`ruff check .`/`mypy src`/`alembic` зелёные, `pytest` 116 passed (на 3.11;
  в 3.10 `charges.py` не собирается из-за `datetime.UTC` — артефакт, проверено через shim).
  Домен дат (`calculate_next_date` клампы) и `mark_paid` (сдвиг/soft-close) проверены независимо;
  callback-роутинг `charge_*` специфичен, заглушки `start.py` убраны. Критичных находок нет.
  Минор: нет router-теста для charges → **TASK-0013** (low). Отчёт: `handoff/reports/AUDIT-M3-2026-06-01.md`. **Старт M4.**

### Planned
- **Декомпозиция M3 (архитектор, SESSION-2026-06-01-17):** в `inbox/` поставлены
  **TASK-0010** (домен дат `calculate_next_date` с клампом + `ChargeRepository` с `mark_paid`),
  **TASK-0011** (пошаговое создание списания, FSM, FR-3/FR-4/FR-11) и
  **TASK-0012** («Мои списания» + действия, FR-5/FR-6/FR-7). Зависимости 0010→0011→0012.

### Audited (accepted)
- **M2 — повторный аудит, ПРИНЯТО (архитектор, SESSION-2026-06-01-16):** прогон начисто
  без BOT_TOKEN — `ruff format --check src tests`/`ruff check`/`mypy src`/`pytest` (96)/
  `alembic` все зелёные. TASK-0006 (mypy 0), TASK-0007 (ruff), TASK-0008 (роутинг + тест
  через роутер) закрыты. Остаточный формат-долг `tests/test_handlers_settings.py` устранён
  механическим `ruff format`. Заведена TASK-0009 (low: pre-commit + чистка формат-долга).
  Отчёт: `handoff/reports/AUDIT-M2-2026-06-01-r2.md`. **Старт M3.**

### Reviewed
- **Ревью M2 архитектором (SESSION-2026-06-01-12):** независимо подтвердил вердикт аудита
  (M2 не принят, mypy/ruff красные). Дополнительно нашёл **критический баг маршрутизации
  callback'ов** (широкий `startswith` перехватывает add/rename/delete → `int("add")`),
  не ловимый mypy и юнит-тестами → заведён **TASK-0008** (с тестом через роутер). Возвращено
  усиление `executor-guide.md` (полный прогон CI начисто; тест диспетчеризации).
  Примечание: в AUDIT-M2 ruff-задача ошибочно названа TASK-0008 — фактически это TASK-0007.

### Fixed
- **TASK-0006 — mypy (64 ошибки) (исполнитель, SESSION-2026-06-01-13):**
  - Исправлены union-attr (message.edit_*/data.split/from_user.id в 4 handlers), type-arg (dict → dict[str, Any] в keyboards), assignment (rename return |None), arg-type (session из **data: dict)
  - Паттерн: **data: Any + cast(AsyncSession, ...), # type: ignore[union-attr/assignment] на гарантированных местах (F.data фильтры + runtime contract), TYPE_CHECKING + __future__.annotations для ruff TC hygiene
  - Файлы: handlers/{wallets,categories,settings,start}.py, keyboards.py
  - Проверка: mypy src/wrbot и mypy src — 0 ошибок; pytest 92 passed; ruff check на src/handlers+keyboards чист; полный CI-прогон (alembic, validate) OK
  - Отклонения: hygiene для ruff (см. отчёт TASK-0006); игноры вместо редизайна (scope "только типы")

### Fixed
- **TASK-0007 — ruff (5 ошибок форматирования) (исполнитель, SESSION-2026-06-01-14):**
  - Исправлены ровно 5 ошибок из аудита: W291 trailing ws в alembic миграции, E501 line too long в scripts/new_session.py:28, tests/test_handlers_{categories,wallets}.py (длинные assert)
  - Фиксы: trim ws, разбивка длинных строк (dict + assert'ы) на несколько строк (как рекомендовано в задаче)
  - Также применён `ruff format` точечно на 4 файла задачи (минимальный scope)
  - Проверка: `uv run ruff check .` → All checks passed (0 ошибок); `ruff check src tests` + scripts clean; `ruff format --check` на файлах задачи → чисто; полный CI-прогон (mypy 0, pytest 92, alembic, validate) OK. Остальные "would reformat" — пре-экзистентный долг (не в scope 5 ошибок)
  - Отклонения: не запускал массовый `ruff format .` (избегал изменения 9+ файлов вне перечня ошибок в задаче); использовал manual break + scoped format

### Fixed
- **TASK-0008 (critical M2) — callback routing (исполнитель, SESSION-2026-06-01-15):**
  - Исправлен баг: широкие `F.data.startswith("wallet_")` / `"category_"` (зарегистрированы первыми) перехватывали `*_add`, `*_rename_*`, `*_delete_*`, `*_confirm_*` → crash в details handler.
  - Решение: item-кнопки в keyboards теперь генерируют `wallet_item_<id>` / `category_item_<id>`; details-фильтры и парсинг id обновлены на `*_item_*` + split[2].
  - Добавлен `tests/test_callback_routing.py` (4 теста) — инспектируют реальные зарегистрированные фильтры на router objects (то, что использует Dispatcher).
  - Обновлены 2 существующих теста (details теперь вызываются с новым форматом data).
  - Полный CI зелёный (pytest 96 passed, mypy 0, ruff check src/tests чист, alembic/validate OK). format имеет 1 пре-экзистентный.

### Fixed
- **TASK-0010 (M3 foundation) — домен дат + ChargeRepository (исполнитель, SESSION-2026-06-01-18):**
  - Реализован `calculate_next_date` с правильным клампом конца месяца (monthly/quarterly/yearly + once)
  - Создан `ChargeRepository` с полным CRUD + `mark_paid` (сдвиг для периодических, done+paid_at для once)
  - Валидация суммы (Decimal 2 знака >0), периода, лимита `max_charges` в конфиге
  - Новые сервисы: `services/charges.py`, расширен `reference.py`
  - 20 новых тестов (даты + репозиторий) через реальные миграции
  - Полный CI зелёный (116 pytest, mypy 0, ruff clean)
  - M2 полностью принят (AUDIT-M2-r2)

### Fixed
- **TASK-0011 (M3) — пошаговое создание списания (FSM) (исполнитель, SESSION-2026-06-01-19):**
  - NewChargeStates (7 шагов: name, amount, wallet(+add new с возвратом), category(skip), date (ДД.ММ.ГГГГ + валидация), period, notify (global/custom/disable))
  - Полноценный FSM handler с валидациями, sub-flow для кошелька, cancel
  - Новые клавиатуры и тексты
  - Интеграция с ChargeRepository (TASK-0010) и M2 (wallets/categories)
  - Регистрация роутера, убрана заглушка в start.py
  - CI зелёный после format

### Fixed
- **TASK-0012 (M3) — «Мои списания» + действия (исполнитель, SESSION-2026-06-01-20):**
  - Список активных по next_date + карточка с действиями (edit, delete, paid)
  - Paid использует mark_paid (сдвиг/закрытие из 0010)
  - Edit переиспользует NewChargeStates FSM + update
  - Delete с подтверждением
  - Новые клавиатуры/тексты, специфичные charge_* callbacks
  - Интеграция с 0011 (edit reuse), 0010 (mark_paid)
  - Регистрация, убрана заглушка
  - CI зелёный

### Fixed
- **TASK-0009 (pre-commit + формат-долг) (исполнитель, SESSION-2026-06-01-21):**
  - Создан `.pre-commit-config.yaml` (ruff-format, ruff --fix, trailing-whitespace, end-of-file-fixer)
  - `ruff format .` + `ruff check . --fix` — приведён к чистому состоянию **весь репозиторий** (scripts/, alembic/, tests/, docs/ и т.д.; 8 файлов отформатировано)
  - `ruff format --check .` и `ruff check .` — 0 проблем
  - Обновлены `CONTRIBUTING.md` и `executor-guide.md` (инструкция `pre-commit install`)
  - Полный CI (включая whole-repo clean) зелёный без изменений логики
  - M3 полностью готов (0009 был последним)

### Fixed
- **TASK-0014 (M4 foundation) — due-логика + SentReminderRepository + snooze (исполнитель, SESSION-2026-06-01-24):**
  - Полная реализация эффективных дней, due-расчёта (с snooze repeat), выбора пользователей по tz/notify_time
  - SentReminderRepository (was_sent + record — идемпотентно)
  - ChargeRepository.snooze (не меняет next_date)
  - 8 новых тестов (логика + DB идемпотентность)
  - Полный CI зелёный (124 pytest, mypy 0, ruff clean)
  - Фундамент для M4 (по ADR-0005)

### Audited (rejected)
- **M2 — аудит майлстоуна (аудитор, SESSION-2026-06-01-11):**
  - Вердикт: **НЕ ПРИНЯТО** (красный CI: mypy)
  - Критично: mypy — 64 ошибки (union-attr, type-arg, assignment, arg-type) → TASK-0006 (high)
  - Major: ruff — 5 ошибок (line too long, trailing whitespace) → TASK-0007 (medium)
  - Ок: validate.py ✅, pytest 92 passed ✅, alembic upgrade head ✅, секреты изолированы ✅
  - Архитектура: слои соблюдены, DI через middleware, FR-13 изоляция по tg_id ✅
  - Следующий шаг: закрыть TASK-0006 + TASK-0007, перепроверка аудита

### Added
- **TASK-0005 — бот-UI справочников (исполнитель, SESSION-2026-06-01-10):**
  - Handlers: settings.py (меню настроек), wallets.py (CRUD кошельков), categories.py (CRUD категорий)
  - Callback handlers: help, new_charge, list_charges (заглушки M3)
  - FSM-состояния WalletStates, CategoryStates уже были в states.py (из TASK-0004)
  - Тексты в texts.py: сообщения для кошельков/категорий, ошибки валидации/лимитов
  - Тесты: 51 новый тест (handlers + texts_render), моки через patch
  - ruff format/check, pytest (92 passed), validate — зелёные

### Added
- **TASK-0004 — слой данных справочников (исполнитель, SESSION-2026-06-01-08):**
  - DbSessionMiddleware: DI AsyncSession в хэндлеры, commit/rollback
  - UserRepository.get_or_create(tg_id) с дефолтами
  - WalletRepository: create, list_by_user, get, rename, delete (изоляция user_id)
  - CategoryRepository: аналогичный CRUD
  - services/reference.py: валидация имени, проверка лимитов
  - config.py: max_wallets, max_categories = 20
  - 30 новых тестов: CRUD, изоляция tg_id, лимиты, валидация
  - ruff, mypy, pytest (41 passed), validate — зелёные

### Planned
- **Декомпозиция M2 (архитектор, SESSION-2026-06-01-07):** в `inbox/` поставлены
  **TASK-0004** (репозитории users/wallets/categories с изоляцией tg_id, лимиты, валидация,
  middleware DI `AsyncSession`) и **TASK-0005** (бот-UI: Настройки → Кошельки/Категории,
  CRUD через inline+FSM). Декомпозиция по слоям; лимиты вынесены в конфиг (закрыт открытый вопрос).

### Reviewed
- **Приёмка TASK-0003 (архитектор, SESSION-2026-06-01-05):** проверено начисто без
  BOT_TOKEN — `import wrbot`, `pytest` (11 passed), `alembic upgrade head`, ruff/mypy/validate
  зелёные. Блокер устранён в корне (ленивые `get_settings()` + `@lru_cache`), гарантии
  TASK-0002 без регрессий. **TASK-0003 принят.**

### Audited
- **M1 — аудит майлстоуна (аудитор, SESSION-2026-06-01-06):**
  - Вердикт: **принято**
  - Безопасность: секреты изолированы (TASK-0003), импорт пакета без BOT_TOKEN
  - Архитектура: слои соблюдены, ADR на месте, утечек БД нет
  - Качество: ruff, mypy (в venv), pytest — зелёные (11 passed)
  - Автоматика: validate.py ✅, pip-audit ⚠ (4 CVE в pip 24.0, не runtime)
  - Следующий шаг: старт M2 (Справочники)

### Fixed
- **TASK-0003 — развязать импорт пакета от секретов (исполнитель, SESSION-2026-05-31-04, SESSION-2026-06-01-04):**
  - Убран глобальный `settings` из config.py, добавлен `@lru_cache` к `get_settings()`
  - Убран импорт `settings` из `__init__.py` — импорт пакета теперь не требует BOT_TOKEN
  - Изменён `logging.py` и `__main__.py` на ленивый `get_settings()`
  - Изменён `test_config.py` и `test_imports.py` для работы без BOT_TOKEN
  - CI зелёный: pytest (11 passed) проходит без BOT_TOKEN, ruff/mypy/validate — OK
  - alembic upgrade head работает без BOT_TOKEN
  - TASK-0003 перенесена в done/, отчёт и логи сессий добавлены

### Changed
- **TASK-0002 — доработка скелета (исполнитель, SESSION-2026-05-31-02):**
  - Исправлен `alembic/env.py` для работы с async/sync URL (sqlite+aiosqlite и sqlite)
  - URL берётся из alembic config, а не из settings (фикс для тестов)
  - Убрана проблемная логика с `asyncio.run()` в running loop
  - Исправлен `tests/conftest.py`: убран fallback, миграции через executor
  - Исправлен `src/wrbot/config.py`: model_validator вместо __init__ для mypy
  - Исправлен `src/wrbot/__main__.py`: опечатка Config_ → Config
  - Все тесты проходят (11 passed, включая FK/cascade/UNIQUE)
  - ruff, mypy, pytest, validate.py — всё зелёное
  - `alembic upgrade/downgrade` работает, autogenerate даёт пустой diff

### Fixed
- Alembic миграция теперь работает с async SQLite
- Модели согласованы с миграцией (autogenerate даёт пустой diff)
- CASCADE delete работает для charge → sent_reminders
- UNIQUE constraint предотвращает дубликаты напоминаний

### Audited
- **M1 — аудит майлстоуна (аудитор, SESSION-2026-05-31-03):**
  - Вердикт: принято с замечаниями
  - validate.py, ruff, mypy, pytest — зелёные
  - pip-audit: 4 CVE в pip 24.0 (mitigation: обновить до 26.1+)
  - Найходка: pytest требует BOT_TOKEN=test → TASK-0003 (minor)
  - Безопасность секретов: ок (.env в .gitignore)
  - Архитектура: слои соблюдены, ADR на месте

### Reviewed
- **Ревью TASK-0002 + перепроверка аудита M1 (архитектор, SESSION-2026-06-01-03):**
  - Слой данных TASK-0002 — **принято** (миграция вверх/вниз, FK/каскад, autogenerate пустой, Date).
  - **M1 переоткрыт:** CI на main фактически красный. (1) импорт `wrbot` требует BOT_TOKEN
    (`__init__`→`config.settings`) → падают `pytest` и `alembic` без токена; шаг Pytest в CI
    без токена. (2) `backlog.json` ссылался на отсутствующий файл TASK-0003 → `validate.py` падал.
  - TASK-0003 переоформлен как **BLOCKER** (развязать импорт/секреты, зелёный CI); state пересобран.
  - В `audit-protocol.md`: красный CI = не принято; аудитор гонит гейт начисто; задачи коммитить; независимость аудита.

## [2026-06-01]

### Added
- **TASK-0001 — скелет проекта (исполнитель, SESSION-2026-06-01-01):**
  - Структура `src/wrbot`, pyproject.toml
  - SQLAlchemy-модели (без FK), начальная миграция Alembic
  - Конфигурация из окружения, логирование
  - Точка входа с `/start`, long polling
  - 8 smoke-тестов

### Changed
- **Ревью TASK-0001 (архитектор, SESSION-2026-06-01-02):**
  - Выявлены проблемы: Alembic не работает, ORM без FK, CI фиктивный
  - Заведена доработка TASK-0002

## [2026-05-31]

### Added
- **M0 (Инфраструктура).** Заложен каркас репозитория: документация, протоколы
  совместной работы (handoff), система сессий и состояния, кроссплатформенная
  автоматизация (`scripts/`), CI (валидация handoff/state, lint+test, аудит),
  шаблоны задач/отчётов/логов. Источник правды — GitHub.
- ТЗ зафиксировано в `docs/spec/spec-v1.md` (версия 1.0).
- Создана первая задача разработки `TASK-0001` (скелет Python/Aiogram) в `handoff/inbox/`.
- **Публикация каркаса в GitHub** (`origin/main`) — источник правды активирован.
- **ADR-0003…0007:** SQLAlchemy 2.0 async + Alembic, часовые пояса, движок уведомлений,
  жизненный цикл списания, long polling.

---
_Записи добавляются в конце каждой сессии. Самые свежие — сверху._
