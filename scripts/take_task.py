"""Берёт верхнюю задачу из inbox/ и переносит в in-progress/. Роль: исполнитель.

Выбор: наименьший номер TASK-XXXX без незакрытых зависимостей (поле depends_on,
если все указанные задачи уже в done/). Перенос через git mv (если есть git).
Печатает содержимое задачи, чтобы исполнитель сразу видел контекст.
"""

from __future__ import annotations

import shutil

import lib


def done_ids() -> set[str]:
    ids = set()
    for path, status in lib.iter_task_files():
        if status == "done":
            tid = lib.task_id_from_name(path.name)
            if tid:
                ids.add(tid)
    return ids


def deps_satisfied(meta: dict, done: set[str]) -> bool:
    raw = meta.get("depends_on", "[]").strip("[] ")
    if not raw:
        return True
    deps = [d.strip() for d in raw.split(",") if d.strip()]
    return all(d in done for d in deps)


def main() -> int:
    candidates = sorted(lib.INBOX.glob("TASK-*.md"), key=lambda p: p.name)
    if not candidates:
        print("inbox пуст — задач нет.")
        return 0
    done = done_ids()
    chosen = None
    for p in candidates:
        if deps_satisfied(lib.parse_frontmatter(p), done):
            chosen = p
            break
    if chosen is None:
        print("Все задачи в inbox имеют незакрытые зависимости. Нужен разбор архитектора.")
        return 1

    dest = lib.IN_PROGRESS / chosen.name
    if lib.in_git_repo():
        lib.git("mv", str(chosen.relative_to(lib.ROOT)), str(dest.relative_to(lib.ROOT)))
    else:
        shutil.move(str(chosen), str(dest))

    # обновим backlog
    import update_state

    update_state.main()

    print(f"Взята задача: {dest.relative_to(lib.ROOT)}\n{'=' * 60}")
    print(dest.read_text(encoding="utf-8"))
    print("=" * 60)
    print(
        "Дальше: выполни задачу, затем python scripts/complete_task.py "
        f"{lib.task_id_from_name(dest.name)} --session SESSION-... --status done"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
