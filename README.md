# wrbot — Telegram-бот «Напоминания об оплатах»

Бот ведёт список будущих списаний пользователя, группирует их по категориям и
кошелькам/картам и присылает напоминания за несколько дней до даты платежа.
Полное ТЗ: [`docs/spec/spec-v1.md`](docs/spec/spec-v1.md).

> **Статус:** инфраструктура заложена (M0). Разработка бота начинается с
> [`handoff/inbox`](handoff/inbox/). Стек: Python 3 · Aiogram 3.x · SQLite/PostgreSQL · APScheduler.

---

## Как устроен этот репозиторий

Это не просто кодовая база, а **управляемый процесс совместной работы двух ролей**:

| Роль | Где работает | Что делает |
|------|--------------|------------|
| **Архитектор** | Cowork (десктоп-приложение Claude) | Ставит задачи, формирует файлы задач в `handoff/inbox`, ревьюит результаты, запускает аудиты |
| **Исполнитель** | Claude Code (CLI) на машине с PAT | Берёт задачу из `handoff/inbox`, выполняет, пишет отчёт, коммитит и пушит в GitHub |

**Источник правды — GitHub.** Обе роли синхронизируются только через `git pull` / `git push`.
Никаких других каналов передачи контекста нет: всё, что нужно знать следующей сессии,
лежит в репозитории в человеко- и машиночитаемом виде.

```
Архитектор (cowork)                 GitHub (источник правды)            Исполнитель (Claude Code)
─────────────────────               ────────────────────────           ─────────────────────────
/new-task  ──► handoff/inbox ──push──►   main branch    ◄──pull── /take-task ──► handoff/in-progress
                                                                         │ выполняет работу в src/
ревью отчёта ◄──pull── handoff/reports ◄──push──   main   ◄──push── /end-session ──► handoff/done
/audit (отдельная сессия) ──► docs/architecture/decisions, reports
```

## Структура каталогов

```
.
├── README.md              ← вы здесь
├── AGENTS.md              ← операционный мануал для ИИ-агентов (читается каждой сессией)
├── .claude/               ← конфиг и слэш-команды Claude Code (CLAUDE.md, commands/)
├── docs/                  ← вся документация
│   ├── spec/              ← ТЗ (исходное требование, неизменяемое)
│   ├── vision.md          ← видение продукта
│   ├── requirements.md    ← структурированные FR/NFR
│   ├── architecture/      ← обзор, модель данных, компоненты, ADR (решения)
│   ├── workflow/          ← протоколы: handoff, сессии, контекст, аудит, гайды ролей
│   ├── roadmap.md         ← майлстоуны и точки аудита
│   ├── glossary.md        ← глоссарий терминов
│   └── templates/         ← шаблоны задач, отчётов, логов сессий, аудитов
├── handoff/               ← конвейер задач (см. handoff/README.md)
│   ├── inbox/             ← новые задачи от архитектора (TODO)
│   ├── in-progress/       ← задача, взятая исполнителем
│   ├── done/              ← выполненные задачи
│   ├── blocked/           ← задачи, ожидающие решения архитектора
│   └── reports/           ← отчёты исполнителя о выполнении
├── sessions/              ← логи сессий (append-only, по одному файлу на сессию)
├── state/                 ← машиночитаемое состояние проекта (project.json, backlog.json, CHANGELOG.md)
├── scripts/               ← кроссплатформенная автоматизация на Python (без ручных команд)
├── .github/               ← CI: валидация handoff/state, lint+test, аудит
├── CHANGELOG.md           ← история версий для пользователей (Keep a Changelog)
└── src/                   ← код самого бота (Python/Aiogram) — появляется с TASK-0001
```

> **Два CHANGELOG:** `/CHANGELOG.md` — для пользователей (история релизов), `state/CHANGELOG.md` — журнал сессий разработчика.

## Быстрый старт

### Локальный запуск бота

Для запуска бота требуется Python 3.11+ и токен Telegram-бота от [@BotFather](https://t.me/BotFather).

```bash
# Клонирование
git clone https://github.com/nmetluk/wrbot.git
cd wrbot

# (Рекомендуется) Установка через uv (быстрее и воспроизводимее)
# uv sync --extra dev
# или классически:
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Создание .env
cp .env.example .env
# Обязательно укажите bot_token и (опционально) database_url

# Применить миграции (один раз или после обновлений)
alembic upgrade head

# Запуск бота
python -m wrbot
```

После запуска бот ответит на `/start`. Логи — в `logs/wrbot.log`.

**Важно:** при каждом запуске (или в Docker entrypoint) автоматически применяются миграции через `alembic upgrade head` (см. `src/wrbot/__main__.py`).

### Развёртывание 24/7 (Docker)

Для production рекомендуется использовать Docker.

```bash
# 1. Настройте .env (bot_token обязателен)
cp .env.example .env

# 2. Запустите (SQLite по умолчанию)
docker compose up -d --build

# С PostgreSQL:
# docker compose --profile postgres up -d --build
```

Подробная инструкция: [`docs/deployment.md`](docs/deployment.md)

Включает:
- Автоматические миграции при старте контейнера
- `restart: unless-stopped`
- Volume для данных SQLite
- Опциональный профиль PostgreSQL

Логи: `docker compose logs -f bot`

### Первичная публикация (один раз)
Репозиторий уже инициализирован и закоммичен локально. Чтобы опубликовать каркас в GitHub:

```bash
python scripts/bootstrap.py            # кроссплатформенно: настроит remote и сделает push
# или вручную:
git push -u origin main
```
Для push нужны учётные данные GitHub (на машине исполнителя — PAT). Подробности:
[`docs/workflow/handoff-protocol.md`](docs/workflow/handoff-protocol.md).

### Цикл работы
- **Архитектор** (в cowork): «возьми задачу архитектора» → формирует задачу через `/new-task`.
- **Исполнитель** (в Claude Code): «возьми задачу исполнителя» → `/take-task` берёт верхнюю задачу из `inbox`.

Полные инструкции ролей:
[`docs/workflow/architect-guide.md`](docs/workflow/architect-guide.md) ·
[`docs/workflow/executor-guide.md`](docs/workflow/executor-guide.md).

## Принципы проекта
1. **GitHub — единственный источник правды.** Контекст не хранится в голове агента, а в репозитории.
2. **Каждый шаг — отдельная сессия.** Перед началом читается `AGENTS.md` + `state/` + последний лог сессии.
3. **Машиночитаемость.** Состояние дублируется в JSON, чтобы следующий агент мгновенно восстановил контекст.
4. **Кроссплатформенность.** LF в репозитории, скрипты на Python, никаких bash-only команд.
5. **Без ручных шагов.** Всё, что можно автоматизировать, автоматизировано в `scripts/` и CI.
6. **Аудит после каждого крупного раздела.** Безопасность, архитектура, качество — в отдельной сессии.
