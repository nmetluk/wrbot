"""Завершает задачу: переносит из in-progress/ в done/ (или blocked/),
создаёт заготовку отчёта и обновляет backlog. Роль: исполнитель.

Пример:
  python scripts/complete_task.py TASK-0001 --session SESSION-2026-05-31-02 --status done
"""
from __future__ import annotations

import argparse
import shutil

import lib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id", help="Например TASK-0001")
    ap.add_argument("--session", required=True, help="ID лога сессии")
    ap.add_argument("--status", choices=["done", "blocked"], default="done")
    args = ap.parse_args()

    matches = list(lib.IN_PROGRESS.glob(f"{args.task_id}-*.md"))
    if not matches:
        print(f"Не найдена задача {args.task_id} в in-progress/.")
        return 1
    src = matches[0]
    target_dir = lib.DONE if args.status == "done" else lib.BLOCKED
    dest = target_dir / src.name

    if lib.in_git_repo():
        lib.git("mv", str(src.relative_to(lib.ROOT)), str(dest.relative_to(lib.ROOT)))
    else:
        shutil.move(str(src), str(dest))

    # заготовка отчёта, если ещё нет
    report = lib.REPORTS / f"{args.task_id}-report.md"
    if not report.exists():
        tpl = (lib.TEMPLATES / "report.template.md").read_text(encoding="utf-8")
        content = (
            tpl.replace("TASK-XXXX", args.task_id)
            .replace("SESSION-YYYY-MM-DD-NN", args.session)
            .replace("YYYY-MM-DDTHH:MM:SSZ", lib.now_utc())
        )
        report.write_text(content, encoding="utf-8")
        print(f"Создана заготовка отчёта: {report.relative_to(lib.ROOT)} — ЗАПОЛНИ ЕЁ.")

    import update_state

    update_state.main()
    print(f"Задача {args.task_id} → {target_dir.name}/")
    print("Не забудь: заполнить отчёт, обновить state/project.json и CHANGELOG.md, "
          "создать лог сессии, закоммитить и запушить.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
