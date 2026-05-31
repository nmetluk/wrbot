---
description: Синхронизация с origin/main и пересборка состояния
---

1. `git fetch origin && git pull --ff-only`.
2. `python scripts/update_state.py` — пересобери `state/backlog.json`.
3. `python scripts/validate.py` — проверь согласованность.
4. Кратко доложи: текущая фаза (`state/project.json`), что в `inbox/`/`in-progress/`,
   чем закончилась последняя сессия (`sessions/`).
