# Отчёт по TASK-0020

- **Исполнитель/сессия:** SESSION-2026-06-01-34
- **Дата:** 2026-06-02T01:10:00Z
- **Итоговый статус:** done

## Что сделано
Реализованы все критерии приёмки TASK-0020. Устранён нондетерминизм гейта CI: теперь и локально, и в CI используются **точно те же** версии инструментов из `uv.lock` (ruff==0.15.15, mypy==2.1.0, pytest==9.0.3 и др.).

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| CI (`.github/workflows/ci.yml`) ставит deps из lock: `uv sync --frozen` (+ `uv run` для команд) | ✅ | Полностью заменён `pip install -e ".[dev]"` + setup-python+pip-cache. Добавлен `astral-sh/setup-uv@v3` + `uv python install 3.11` + `uv sync --frozen --extra dev`. Все шаги (ruff, mypy, pytest, alembic, validate, scripts) — через `uv run`. |
| Локальный и CI прогоны используют одни и те же версии ruff/mypy из `uv.lock` | ✅ | Воспроизведено локально на чистом `.venv` (Python 3.11.15 + pinned tools). `uv run ruff --version` = 0.15.15, mypy 2.1.0. |
| `executor-guide.md` / `CONTRIBUTING.md` явно требуют `uv run` (как в CI) | ✅ | Обновлены разделы "Обязательный прогон CI" и "Качество кода": приведены точные команды с `uv run`, пример `uv sync --frozen --extra dev`. |
| (Опц.) Зафиксировать верхние границы в pyproject | ⏸️ | Не делалось — lock является источником правды (как решено в аудите). Опционально, не требуется для acceptance. |
| Весь CI начисто зелёный на зафиксированных версиях | ✅ | Полный локальный прогон команд из ci.yml (после `uv sync --frozen --extra dev`) — все 0 exit code. |

## Как проверено
- **Локальная симуляция CI начисто (ровно команды из ci.yml, чистый env, Python 3.11.15 из uv, без лишних pip):**
  ```
  uv sync --frozen --extra dev
  uv run ruff format --check src tests   → 53 files already formatted (0)
  uv run ruff check src tests            → All checks passed! (0)
  uv run mypy src                        → Success: no issues... (0)
  uv run pytest                          → 145 passed (0)
  BOT_TOKEN=test uv run alembic upgrade head → OK (0, SQLite)
  uv run python scripts/validate.py      → Валидация пройдена (0)
  uv run ruff check scripts && uv run python -m py_compile scripts/*.py → OK
  ```
  (Два прогона: до/после clean `rm -rf .venv`; оба зелёные. Выводы сохранены в логе сессии.)

- **Handoff/state:** `python3 scripts/validate.py` — зелёно (до и после complete).

- **Ручная:** git status чист (кроме ожидаемых артефактов сессии), pre-commit не ломает.

- CI на GitHub будет запущен автоматически после push'а (ожидается зелёный).

## Затронутые файлы
- `.github/workflows/ci.yml` (основное изменение)
- `docs/workflow/executor-guide.md`
- `CONTRIBUTING.md`
- `state/project.json`, `state/CHANGELOG.md`, `state/backlog.json` (процесс)
- `handoff/in-progress/...` → `handoff/done/TASK-0020-....md` (mv)
- `sessions/SESSION-2026-06-01-34.md`
- `handoff/reports/TASK-0020-report.md`

## Отклонения от задачи
- Не создавал `.python-version` (uv резолвит из pyproject/lock; CI явно делает `uv python install 3.11` — достаточно).
- Не трогал `README.md` (install-пайплайн) и `.pre-commit-config.yaml` — за рамками минимального scope критериев (можно отдельной задачей).
- Нет нового ADR (изменение инфраструктурное, документировано в задаче + отчёте + сессии).
- Python в CI: 3.11 (как раньше), runtime в локальной .venv после clean — тоже 3.11.15.

## Открытые вопросы / следующий шаг
- Следующий для исполнителя: `/take-task` → TASK-0021 (M5 resilience/errors).
- После всех M5 (0020-0024) — отдельная сессия финального комплексного аудита перед релизом.
- (Будущее) При желании: добавить `.python-version`, обновить README quickstart на uv-first, починить deprecation в alembic config (не blocker).

## Коммиты
- `ci(TASK-0020): deterministic toolchain via uv sync --frozen + uv run` (Task: TASK-0020)
  Изменения: ci.yml, executor-guide, CONTRIBUTING, state/, handoff/, sessions/, reports/.
