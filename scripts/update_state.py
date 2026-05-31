"""Пересобирает state/backlog.json из фактического содержимого handoff/.

Генерируемый файл — НЕ редактировать руками. Запускать после любого перехода
задачи между каталогами. Используется CI (validate.yml).
"""
from __future__ import annotations

import lib


def build_backlog() -> dict:
    tasks = []
    counts = {"inbox": 0, "in_progress": 0, "done": 0, "blocked": 0}
    for path, status in lib.iter_task_files():
        meta = lib.parse_frontmatter(path)
        tid = lib.task_id_from_name(path.name) or meta.get("id", "")
        report = lib.REPORTS / f"{tid}-report.md"
        tasks.append(
            {
                "id": tid,
                "title": meta.get("title", ""),
                "status": status,
                "file": str(path.relative_to(lib.ROOT)).replace("\\", "/"),
                "milestone": meta.get("milestone", ""),
                "report": (
                    str(report.relative_to(lib.ROOT)).replace("\\", "/")
                    if report.exists()
                    else None
                ),
            }
        )
        counts[status] += 1
    tasks.sort(key=lambda t: t["id"])
    return {
        "generated_by": "scripts/update_state.py",
        "generated_at": lib.now_utc(),
        "note": "Генерируемый файл. Не редактировать вручную. Источник — каталоги handoff/.",
        "counts": counts,
        "tasks": tasks,
    }


def main() -> int:
    backlog = build_backlog()
    lib.write_json(lib.STATE / "backlog.json", backlog)
    print(
        f"backlog.json обновлён: "
        f"inbox={backlog['counts']['inbox']} "
        f"in_progress={backlog['counts']['in_progress']} "
        f"done={backlog['counts']['done']} "
        f"blocked={backlog['counts']['blocked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
