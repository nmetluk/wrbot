"""Создаёт файл лога сессии из шаблона. Возвращает его id и путь.

Пример:
  python scripts/new_session.py --role executor
"""

from __future__ import annotations

import argparse

import lib


def next_session_id() -> str:
    day = lib.today()
    existing = sorted(lib.SESSIONS.glob(f"SESSION-{day}-*.md"))
    n = len(existing) + 1
    return f"SESSION-{day}-{n:02d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["architect", "executor", "auditor"], required=True)
    args = ap.parse_args()

    sid = next_session_id()
    dest = lib.SESSIONS / f"{sid}.md"
    tpl = (lib.TEMPLATES / "session-log.template.md").read_text(encoding="utf-8")
    role_ru = {
        "architect": "архитектор",
        "executor": "исполнитель",
        "auditor": "аудитор",
    }[args.role]
    content = tpl.replace("SESSION-YYYY-MM-DD-NN", sid).replace(
        "архитектор | исполнитель | аудитор", role_ru
    )
    dest.write_text(content, encoding="utf-8")
    print(sid)
    print(f"Лог сессии: {dest.relative_to(lib.ROOT)} — заполни по ходу/в конце сессии.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
