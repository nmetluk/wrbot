---
id: TASK-0025
title: "M5: выбор часового пояса в Настройках (корректное время для не-МСК)"
milestone: M5
status: inbox
priority: high
created_by: architect
created_at: 2026-06-01T23:30:00Z
depends_on: [TASK-0005]
---

# TASK-0025: UI смены часового пояса

## Цель
Дать пользователю выбрать часовой пояс в «⚙️ Настройки», чтобы напоминания приходили в
корректное локальное `notify_time` (решение владельца: включить в v1). ADR-0004.

## Контекст
- Поле `users.tz` уже есть (дефолт `Europe/Moscow`); свип уже считает время по `tz` (M4).
- Не хватает только UI смены и сохранения. Готово: меню «Настройки» (M2), `UserRepository`.
- Уроки: специфичные callback-фильтры + router-тест (TASK-0008); тексты в `texts.py`; моки autospec.

## Критерии приёмки (проверяемые)
- [ ] В «⚙️ Настройки» — пункт «🕒 Часовой пояс» с текущим значением и выбором из
      курируемого списка основных российских поясов (IANA): Europe/Kaliningrad, Europe/Moscow,
      Europe/Samara, Asia/Yekaterinburg, Asia/Omsk, Asia/Krasnoyarsk, Asia/Irkutsk, Asia/Yakutsk,
      Asia/Vladivostok, Asia/Magadan, Asia/Kamchatka (можно с подписями смещения).
- [ ] Выбор сохраняется в `users.tz` (метод `UserRepository`, напр. `set_tz`/`update`), изоляция по tg_id;
      валидация значения через `zoneinfo.ZoneInfo` (некорректное — отклонить).
- [ ] Специфичные callback'и (напр. `settings_tz`, `tz_set_<Area/City>`), без перехвата чужих;
      **router-тест** на маршрутизацию; `/cancel` корректно завершает.
- [ ] Тексты — только в `texts.py`; ≥1 тест реального рендера (если есть подстановки).
- [ ] Тесты: сохранение tz, валидация, изоляция, роутинг. Весь CI начисто зелёный.

## Ожидаемые артефакты
- Код: правки `handlers/settings.py`, `keyboards.py`, `texts.py`, `UserRepository`; регистрация.
- Тесты: `tests/test_handlers_timezone.py` (+ router/render).

## Ограничения / заметки
- Список поясов — курируемый (не весь IANA), для простоты UI (§1.3). Перед `done`: полный CI, отчёт, лог, push.

## Зависимости
Зависит от: TASK-0005
