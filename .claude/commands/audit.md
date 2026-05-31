---
description: Комплексный аудит майлстоуна в отдельной сессии (безопасность/архитектура/качество)
---

Ты — аудитор. Действуй независимо, как ревьюер, не доверяя «на слово».

1. `git pull --ff-only`. Прочитай `docs/workflow/audit-protocol.md` и `docs/roadmap.md`
   (какой майлстоун аудируем).
2. Создай лог сессии: `python scripts/new_session.py --role auditor`.
3. Прогони автоматику: `python scripts/validate.py`, `ruff check`, `mypy`, `pytest`,
   аудит зависимостей (`pip-audit` или `safety`), поиск секретов в истории
   (`git log -p | grep`-эвристики, наличие `.env` вне `.gitignore`).
4. Проверь по направлениям: безопасность, архитектура (соответствие ADR и слоям),
   качество кода, трассировка FR/NFR ↔ код ↔ тесты, надёжность 24/7, целостность
   процесса (`handoff/`, `state/`, логи).
5. Заполни отчёт по `docs/templates/audit-report.template.md`, сохрани как
   `handoff/reports/AUDIT-Mx-YYYY-MM-DD.md`.
6. Каждую находку оформи задачей в `handoff/inbox/` (`scripts/new_task.py`),
   критичные по безопасности — с пометкой high priority.
7. Зафиксируй вердикт в `state/CHANGELOG.md`, заверши через `/end-session`.

Майлстоун принят только при отсутствии критичных находок (или после их закрытия и перепроверки).
