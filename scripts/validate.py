"""Проверка целостности процесса (для CI и локального запуска).

Проверяет:
  1. backlog.json соответствует фактическому содержимому handoff/.
  2. Имена файлов задач корректны и id уникальны.
  3. Каждая задача в done/ имеет отчёт в reports/.
  4. project.json валиден и содержит обязательные поля.
Возвращает ненулевой код при любой ошибке.
"""

from __future__ import annotations

import json

import lib
from update_state import build_backlog

REQUIRED_PROJECT_FIELDS = [
    "project",
    "updated_at",
    "current_milestone",
    "last_session",
    "next_step",
]


def main() -> int:
    errors: list[str] = []

    # 1. backlog.json в актуальном состоянии
    expected = build_backlog()
    backlog_path = lib.STATE / "backlog.json"
    if not backlog_path.exists():
        errors.append("state/backlog.json отсутствует")
    else:
        actual = lib.read_json(backlog_path)
        # сравниваем без временной метки
        if actual.get("tasks") != expected["tasks"] or actual.get("counts") != expected["counts"]:
            errors.append(
                "state/backlog.json не соответствует handoff/. "
                "Запусти: python scripts/update_state.py"
            )

    # 2. имена задач и уникальность id
    seen: dict[str, str] = {}
    for path, _ in lib.iter_task_files():
        tid = lib.task_id_from_name(path.name)
        if not tid:
            errors.append(f"Некорректное имя файла задачи: {path.name}")
            continue
        if tid in seen:
            errors.append(f"Дубликат id {tid}: {seen[tid]} и {path.name}")
        seen[tid] = path.name

    # 3. отчёты для done/
    for path, status in lib.iter_task_files():
        if status != "done":
            continue
        tid = lib.task_id_from_name(path.name)
        if tid and not (lib.REPORTS / f"{tid}-report.md").exists():
            errors.append(f"{tid} в done/ без отчёта reports/{tid}-report.md")

    # 4. project.json
    pj = lib.STATE / "project.json"
    if not pj.exists():
        errors.append("state/project.json отсутствует")
    else:
        try:
            data = lib.read_json(pj)
            for f in REQUIRED_PROJECT_FIELDS:
                if f not in data:
                    errors.append(f"project.json: нет обязательного поля '{f}'")
        except json.JSONDecodeError as e:
            errors.append(f"project.json не парсится: {e}")

    if errors:
        print("ВАЛИДАЦИЯ НЕ ПРОЙДЕНА:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Валидация пройдена: handoff/ и state/ согласованы.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
