"""Создаёт новый файл задачи в handoff/inbox/ из шаблона. Роль: архитектор.

Пример:
  python scripts/new_task.py --title "Скелет проекта" --slug project-skeleton --milestone M1
"""

from __future__ import annotations

import argparse

import lib


def slugify(text: str) -> str:
    import re

    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "task"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True, help="Заголовок задачи")
    ap.add_argument("--slug", help="Латиницей для имени файла (по умолчанию из title)")
    ap.add_argument("--milestone", default="", help="Например M1")
    ap.add_argument("--depends-on", default="", help="Через запятую: TASK-0001,TASK-0002")
    args = ap.parse_args()

    number = lib.next_task_number()
    tid = f"TASK-{number:04d}"
    slug = args.slug or slugify(args.title)
    # если slug латиницей не вышел (кириллица), подстрахуемся
    if not slug or not slug.isascii():
        slug = f"task-{number:04d}"
    fname = f"{tid}-{slug}.md"
    dest = lib.INBOX / fname

    tpl = (lib.TEMPLATES / "task.template.md").read_text(encoding="utf-8")
    depends = (
        "[" + ", ".join(d.strip() for d in args.depends_on.split(",") if d.strip()) + "]"
        if args.depends_on
        else "[]"
    )
    content = (
        tpl.replace("TASK-XXXX", tid)
        .replace("<краткое название>", args.title)
        .replace("<название>", args.title)
        .replace("milestone: Mx", f"milestone: {args.milestone}")
        .replace("created_at: YYYY-MM-DDTHH:MM:SSZ", f"created_at: {lib.now_utc()}")
        .replace("depends_on: []", f"depends_on: {depends}")
    )
    dest.write_text(content, encoding="utf-8")
    print(f"Создана задача: {dest.relative_to(lib.ROOT)}")
    print("Отредактируй цель/критерии приёмки, затем: python scripts/update_state.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
