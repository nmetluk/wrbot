---
description: Корректно завершить сессию с сохранением контекста и push в GitHub
---

Заверши сессию так, чтобы следующий агент/человек восстановил контекст ТОЛЬКО из репозитория:

1. Если работал над задачей — заполни отчёт `handoff/reports/TASK-XXXX-report.md`
   (что сделано по каждому критерию, как проверено, отклонения, коммиты). Перенос
   задачи: `python scripts/complete_task.py TASK-XXXX --session <SESSION-id> --status done|blocked`.
2. Обнови `state/project.json`: `updated_at` (UTC), `current_phase`/`current_milestone`,
   `active_task`, `last_session` (твой SESSION-id), `next_step` (что делать дальше).
3. `python scripts/update_state.py` — пересобери `state/backlog.json`.
4. Допиши `state/CHANGELOG.md` (раздел Added/Changed/Fixed).
5. Заполни лог сессии `sessions/<SESSION-id>.md` (цель, что сделано, решения, следующий шаг, коммиты).
6. Проверь целостность: `python scripts/validate.py` (должно быть зелено).
7. Закоммить (Conventional Commits, `Task: TASK-XXXX`) и **запушь**: `git push`.

Перед push спроси себя: «Достаточно ли в репозитории, чтобы продолжить с нуля?»
Если нет — дополни логи/состояние.
