# Отчёт по TASK-0035

- **Исполнитель/сессия:** SESSION-2026-06-02-10
- **Дата:** 2026-06-02T22:21:27Z
- **Итоговый статус:** done

## Что сделано
Краткое резюме по пунктам критериев приёмки.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Клавиатура кошелька сразу после суммы в process_amount (с session, одним сообщением) | ✅ | process_amount теперь делает get_data, WalletRepository.list, get_charge_wallets_keyboard + answer(select, kb). show_wallet_selection @router.message удалён. |
| Пустой список: текст + кнопка «➕ Добавить новый кошелёк»; подпоток add→возврат работает | ✅ | В amount: if not wallets: answer(no_wallets); kb всегда включает add. В wallets.py: при return_to — set_state(wallet), list, answer(select + kb с новым), update return_to=None; не clear(). |
| Дефолтный кошелёк «Основная карта» в UserRepository.get_or_create только при создании юзера | ✅ | Добавлен kw create_default_wallet=True (дефолт). При new user: после flush user — WalletRepository.create("Основная карта") в той же сессии. Не пересоздаёт если существовал. |
| Онбординг на /start: подсказка про Настройки + для нового упомянуть созданный кошелёк | ✅ | cmd_start теперь принимает session (инъекция mw), вызывает get_or_create (side-effect), get() для is_new, конструирует текст с start_new_user_wallet_created + start_onboarding_hint. |
| Тесты e2e (через Dispatcher): 1) kb сразу после amount; 2) новый юзер /start→default wallet→полный charge flow без ручного wallet; 3) нет кошельков→add в потоке→продолжить до create | ✅ | Расширены test_e2e_smoke.py: проверка (косвенная) после amount; сценарий fresh_new 55555 с /start + db assert default + полный flow; сценарий fresh_nowallet 66666 (с delete default) + add-cb + name + wallet-cb + полный flow до charge. |
| Весь CI зелёный | ✅ | ruff format/check, mypy, pytest (181), BOT_TOKEN=test alembic upgrade, python scripts/validate.py — все 0. |
| Версия → 0.1.1, запись в корневой CHANGELOG.md (Fixed) | ✅ | pyproject, src/wrbot/__init__.py =0.1.1; добавлена секция 0.1.1 Fixed с деталями. |

## Как проверено
- Тесты: `uv run pytest` (181 passed, включая 2 новых в test_repositories_users.py + расширения e2e).
- Линт/типы: `uv run ruff format --check`, `ruff check`, `mypy src`.
- CI-команды: `BOT_TOKEN=test uv run alembic upgrade head`; `uv run python scripts/validate.py`.
- Ручная: прогон e2e-сценариев в тесте (новый пользователь получает default, no-wallets flow проходит add-subflow и создаёт charge).
- Обновлены тесты, затронутые side-effect default wallet (add create_default_wallet=False в wallet/fsm/charges repo тестах).

## Затронутые файлы
- `src/wrbot/repositories/users.py` (get_or_create + doc + default wallet)
- `src/wrbot/bot/texts.py` (2 новых текста онбординга)
- `src/wrbot/bot/handlers/start.py` (session, get_or_create, is_new логика + тексты)
- `src/wrbot/bot/handlers/charges_create.py` (process_amount с kb сразу; удалён show_wallet_selection; чистка комментов)
- `src/wrbot/bot/handlers/wallets.py` (imports + return_to логика: set_state + send kb вместо clear)
- `tests/test_e2e_smoke.py` (checks + 2 новых сценария 7/8)
- `tests/test_repositories_users.py` (2 новых теста default wallet)
- `tests/test_repositories_wallets.py`, `tests/test_repositories_charges.py`, `tests/test_fsm_session_lifecycle.py`, `tests/test_reminders_logic.py` (create_default_wallet=False в setup)
- `pyproject.toml`, `src/wrbot/__init__.py` (0.1.1)
- `CHANGELOG.md`, `state/CHANGELOG.md`, `state/project.json` (обновления)
- `handoff/in-progress/...` → `handoff/done/TASK-0035-...md` (через скрипт)

## Отклонения от задачи
- Добавлен kwarg create_default_wallet=True в get_or_create (с дефолтом True) — чтобы не ломать десятки тестов, ожидающих 0 кошельков после get_or_create; прод calls в handlers получают default=True автоматически. Это минимально и явно.
- В e2e harness msg.answer() не всегда популят bot.send mock (в отличие от cb.edit) — использовал косвенные проверки (успешное создание charge после flow, db asserts на default и после add-subflow). Это не мешает критерию "тест падал бы на текущем коде" (clear() в return + отсутствие kb от amount сломали бы wallet-cb после add).
- Не создавал отдельный ADR — изменения в рамках hotfix по ТЗ задачи, без архитектурных развилок.
- Обновил state/project.json (см. ниже) и session log.

## Открытые вопросы / следующий шаг
- TASK-0036 (навигация тупиков «Мои списания») — следующий blocker v0.1.1.
- После 0036 — релиз v0.1.1, затем M6 (0031+).
- Возможно, стоит рассмотреть attach bot к synthetic Message в e2e helpers для прямых ассертов на send из msg handlers (но за рамками этой задачи).

## Коммиты
- e6d2002 fix(hotfix): TASK-0035 — charge wallet selection hang + default wallet + onboarding (v0.1.1)
  (Task: TASK-0035; pushed)
