---
id: TASK-0003
title: Развязать импорт пакета и секреты; зелёный CI без BOT_TOKEN
milestone: M1
status: inbox
created_by: architect
created_at: 2026-05-31T23:34:30Z
depends_on: [TASK-0002]
---

# TASK-0003: Развязать импорт пакета и секреты; честно зелёный CI

## Цель
Сделать так, чтобы **импорт пакета `wrbot` не требовал секретов** (BOT_TOKEN), и
CI-гейт, введённый TASK-0002, был **реально зелёным** (включая шаг `pytest` без
BOT_TOKEN). Это разблокирует закрытие M1.

## Контекст / приоритет
- **Severity: BLOCKER** (не minor). Найдено при архитектурном ревью TASK-0002
  (SESSION-2026-06-01-03), уточняет находку аудита M1 (SESSION-2026-05-31-03).
- Связанные ADR: ADR-0003 (слой данных), ADR-0004 (config), NFR-6 (секреты в окружении).

## Корень проблемы (подтверждено прогоном)
`src/wrbot/__init__.py` выполняет `from wrbot.config import settings`, а `config.py`
на уровне модуля делает `settings = get_settings()` → **любой импорт `wrbot` требует
BOT_TOKEN**. Последствия:
- `pytest` без BOT_TOKEN падает на сборке (conftest импортирует `wrbot`).
- `alembic upgrade head` без BOT_TOKEN падает (`env.py` импортирует `wrbot.db.models` → пакет).
- В `ci.yml` шаг **Pytest** запускается без BOT_TOKEN → **CI красный на main**.
- Импорт кода связан с runtime-секретом — архитектурный запах.

## Критерии приёмки (проверяемые)
- [ ] **Импорт `wrbot` и любых подпакетов НЕ требует BOT_TOKEN.** Убрать создание
      `settings` на уровне модуля и `from wrbot.config import settings` из `__init__.py`.
      Настройки получать лениво (`get_settings()` с кэшем, например `functools.lru_cache`)
      в точке использования (`__main__.py` и т.п.), не при импорте.
- [ ] `python -c "import wrbot; import wrbot.db.models"` **без** BOT_TOKEN — успех.
- [ ] `pytest` **без** BOT_TOKEN в окружении — зелёный (тесты, которым нужен токен,
      получают его через fixture/monkeypatch, а не из глобального окружения).
- [ ] `alembic upgrade head` **без** BOT_TOKEN — успех (env.py импортирует только модели,
      не настройки приложения).
- [ ] `ci.yml`: шаг Pytest не зависит от BOT_TOKEN (или явно его не требует); все шаги
      проходят. CI на main — зелёный.
- [ ] Сохранены гарантии TASK-0002: FK/каскад, Date-типы, autogenerate-diff пустой,
      `bot_token` по-прежнему обязателен **в рантайме бота** (бот не стартует без токена).
- [ ] `python scripts/validate.py` — зелёный (state согласован с handoff).

## Ожидаемые артефакты
- Код: `src/wrbot/__init__.py`, `src/wrbot/config.py`, при необходимости `__main__.py`, `tests/conftest.py`.
- CI: `.github/workflows/ci.yml` (шаг pytest без зависимости от секрета).
- Тест: импорт пакета без секретов (smoke), напр. `tests/test_imports.py`.

## Ограничения / заметки
- Не выходи за scope: только развязка импорта/секретов и зелёный CI. Бизнес-логику не трогать.
- Рантайм бота обязан падать с понятной ошибкой, если BOT_TOKEN не задан (NFR-6).
- Перед `done`: отчёт, лог сессии (**уникальный ID**, не перезаписывать чужой), state, push.
- Дата в логах/отчётах — в UTC; следи, чтобы локальные часы машины не уводили нумерацию назад.

## Зависимости
Зависит от: TASK-0002
