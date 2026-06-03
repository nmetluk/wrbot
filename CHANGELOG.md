# Changelog

История версий wrbot для пользователей. Формат основан на [Keep a Changelog](https://keepachangelog.com/).

## [0.1.1] - 2026-06-03

### Fixed
- **HOTFIX v0.1.1 (blocker, TASK-0035):** создание списания зависало на шаге «Выберите кошелёк» — `process_amount` отправлял «Загружаю список...», клавиатуру рендерил только `@router.message(NewChargeStates.wallet)` (требовал доп. сообщения, которого не было). Теперь клавиатура (с кнопкой «➕ Добавить новый кошелёк») показывается сразу после ввода суммы в одном сообщении.
- Дефолтный кошелёк «Основная карта» создаётся автоматически при создании нового пользователя в `UserRepository.get_or_create` (идемпотентно, только при создании юзера, в той же транзакции; не пересоздаётся после удаления).
- Онбординг на `/start`: для нового пользователя упоминается созданный «Основная карта»; всегда — подсказка, что кошельки и категории настраиваются в «⚙️ Настройки».
- Исправлен возврат из подпотока «Добавить кошелёк» внутри создания списания (раньше `state.clear()` обрывал flow) — теперь возвращает к выбору кошелька с kb сразу.
- Дополнены e2e-тесты (через Dispatcher): проверка немедленной клавиатуры после суммы; сценарий нового пользователя (дефолт + полный flow без ручного кошелька); сценарий «нет кошельков → добавить в потоке → продолжить создание».
- Версия 0.1.1 (pyproject, `__init__`); записи в CHANGELOG.
- **TASK-0036:** навигационные тупики «Мои списания» + ревизия reply_markup=None (кнопки new_charge/main_menu; post-action возвраты с меню).
- **TASK-0031 (M6 start):** конфиг `ADMIN_CHANNEL_ID`/`ADMIN_TZ`; `AdminNotifier` (send_text/photo/media_group, no-op, error isolation, secret sanitization). Фундамент для observability (0032-0034).
- **TASK-0032:** audit_log таблица + запись действий (без sensitive), дублирование критичных ошибок в админ-канал.
- **TASK-0033:** ежечасный бэкап (VACUUM/pg_dump, ротация 36) + heartbeat + сводка в админ-канал; docker support.
- **TASK-0034:** ежедневный дашборд 21:00 в ADMIN_TZ — расширенные метрики (stats) + 8 графиков (matplotlib Agg, PNG bytes), отправка саммари + альбом в админ-канал; инструментация audit для sent reminders + critical errors; тесты, полный CI.
- **TASK-0037:** UX consistency (low): removed duplicate «❌ Закрыть» (cancel) from «Мои списания» kb (and views); «Отмена»/cancel only in active dialogs (now always «Действие отменено» + main menu kb, no orphans). E2E via feed_update + prompt kb fixes. CI green.
- **TASK-0038 (M6 blocker fix):** made backup test hermetic (create_backup now accepts explicit db_url=; autouse fixture + manual cache_clear for get_settings lru_cache; pass temp DB from test_engine). Full pytest now deterministic (208 passed, no order deps). CI green. Prepares for re-audit + v0.2.0.

## [0.1.0] - 2026-06-03

Первый релиз. Полный объём v1 по ТЗ (§1–§5). Принят релиз-аудитом
(`handoff/reports/AUDIT-M5-2026-06-02-r3.md`).

### Added
- **Главное меню** `/start`, команды `/help`, `/cancel` (FR-1, FR-2).
- **Списания (CRUD):** пошаговое создание (название, сумма, кошелёк, категория, дата,
  периодичность, настройка уведомлений), «Мои списания» (список по дате), редактирование,
  удаление, «Отметить оплаченным» со сдвигом даты на период / закрытием одноразовых (FR-3…FR-7).
- **Справочники:** кошельки/карты и категории — полный CRUD в «Настройках» (FR-8, FR-9).
- **Уведомления:** напоминания в выбранное время с кнопками «Оплачено»/«Отложить»/«Редактировать»;
  глобальные и индивидуальные дни; «Отложить» не сдвигает дату платежа (FR-10, FR-11, FR-12).
- **Глобальные настройки:** время уведомлений, дни напоминаний, выбор часового пояса.
- **Изоляция данных** по `tg_id`; интерфейс на русском (FR-13, FR-14).
- **Надёжность 24/7:** периодический свип по БД (рестарт-безопасный, идемпотентный),
  глобальный обработчик ошибок, graceful shutdown (NFR-1, NFR-2).
- **Развёртывание:** Dockerfile + docker-compose (профиль PostgreSQL), миграции при старте,
  `docs/deployment.md`.

### Technical
- Python 3.11+, aiogram 3.x (long polling), SQLAlchemy 2.0 async + Alembic, APScheduler.
- SQLite (старт) / PostgreSQL; конфигурация и секреты — через окружение (`.env`).
- Качество: ruff, mypy (strict), pytest (179 тестов), детерминированный CI через `uv.lock`.
