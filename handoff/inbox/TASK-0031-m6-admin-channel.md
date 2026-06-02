---
id: TASK-0031
title: "M6: админ-канал и сервис уведомлений + конфиг (фундамент наблюдаемости)"
milestone: M6
status: inbox
priority: high
created_by: architect
created_at: 2026-06-03T03:30:00Z
depends_on: [TASK-0021]
---

# TASK-0031: Админ-канал и сервис уведомлений

## Цель
Заложить фундамент M6: конфиг админ-канала и сервис отправки в него (текст/фото), с
безопасным no-op при отсутствии канала. На этом строятся бэкапы/аудит/дашборд.

## Контекст
- ADR-0008 (админ-канал, no-op без ID, санитизация, джобы на общем планировщике).
- Готово: `aiogram.Bot`, `setup_scheduler()`/`register_*` в `scheduler/app.py`, конфиг pydantic-settings.

## Критерии приёмки (проверяемые)
- [ ] Конфиг (`config.py`): `ADMIN_CHANNEL_ID: int | None = None`, `ADMIN_TZ: str = "Europe/Moscow"`.
      `.env.example` дополнен (UPPERCASE, как принято в TASK-0029). Секрет не требуется для тестов.
- [ ] `services/admin_notify.py`: `AdminNotifier` (или функции) с `send_text(...)`,
      `send_photo(bytes/...)`, `send_media_group(...)`. Если `ADMIN_CHANNEL_ID` не задан — **no-op**
      (лог debug, без падения). Ошибки отправки **изолированы** (не роняют вызвавшую джобу), логируются.
- [ ] **Санитизация:** утилита, гарантирующая, что в сообщения не попадают `BOT_TOKEN`/креды из
      `DATABASE_URL`/секреты (тест на маскирование).
- [ ] Тесты: no-op без ID; вызов `bot.send_message` с правильным chat_id когда ID задан (mock Bot,
      autospec); изоляция ошибки; маскирование секретов.
- [ ] Весь CI начисто зелёный (`uv run` ruff/mypy/pytest/alembic/validate).

## Ожидаемые артефакты
- Код: `src/wrbot/services/admin_notify.py`, правки `config.py`, `.env.example`.
- Тесты: `tests/test_admin_notify.py`.

## Ограничения / заметки
- Без бизнес-логики бэкапов/аудита/статистики — только канал и отправка. Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0021
