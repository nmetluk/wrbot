"""Первичная публикация репозитория в GitHub (выполнить один раз).

Идемпотентно: init (если нужно), настройка remote origin, первый коммит,
push в main. Требует настроенных учётных данных GitHub (на машине исполнителя — PAT).

  python scripts/bootstrap.py --remote https://github.com/nmetluk/wrbot.git
"""
from __future__ import annotations

import argparse

import lib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--remote",
        default="https://github.com/nmetluk/wrbot.git",
        help="URL удалённого репозитория",
    )
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()

    if not lib.in_git_repo():
        lib.git("init")
        lib.git("checkout", "-b", args.branch, check=False)

    # remote origin
    r = lib.git("remote", check=False)
    if "origin" not in r.stdout.split():
        lib.git("remote", "add", "origin", args.remote)
    else:
        lib.git("remote", "set-url", "origin", args.remote)

    # коммит, если есть что коммитить
    lib.git("add", "-A")
    status = lib.git("status", "--porcelain")
    if status.stdout.strip():
        lib.git("commit", "-m", "chore: bootstrap project scaffold (M0)")
        print("Создан первый коммит.")
    else:
        print("Нет изменений для коммита.")

    push = lib.git("push", "-u", "origin", args.branch, check=False)
    if push.returncode == 0:
        print(f"Каркас опубликован в {args.remote} ({args.branch}).")
        return 0
    print("PUSH НЕ ВЫПОЛНЕН (нужны учётные данные GitHub / PAT):")
    print(push.stderr.strip())
    print("Настрой доступ и повтори: git push -u origin " + args.branch)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
