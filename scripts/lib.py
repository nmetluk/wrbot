"""Общие помощники для скриптов автоматизации wrbot.

Кроссплатформенно (pathlib, без bash-специфики). Python 3.9+.
Источник правды по состоянию задач — каталоги handoff/.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

# Корень репозитория = родитель каталога scripts/
ROOT = Path(__file__).resolve().parent.parent

HANDOFF = ROOT / "handoff"
INBOX = HANDOFF / "inbox"
IN_PROGRESS = HANDOFF / "in-progress"
DONE = HANDOFF / "done"
BLOCKED = HANDOFF / "blocked"
REPORTS = HANDOFF / "reports"
SESSIONS = ROOT / "sessions"
STATE = ROOT / "state"
TEMPLATES = ROOT / "docs" / "templates"

# Каталог -> статус в backlog.json
DIR_STATUS = {
    INBOX: "inbox",
    IN_PROGRESS: "in_progress",
    DONE: "done",
    BLOCKED: "blocked",
}

TASK_RE = re.compile(r"^TASK-(\d{4})-[a-z0-9-]+\.md$")


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parse_frontmatter(path: Path) -> dict:
    """Минимальный парсер YAML-фронтматтера между двумя строками '---'."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def iter_task_files():
    """Возвращает (path, status) для всех файлов задач во всех каталогах handoff."""
    for directory, status in DIR_STATUS.items():
        if not directory.exists():
            continue
        for p in sorted(directory.glob("TASK-*.md")):
            yield p, status


def task_id_from_name(name: str) -> str | None:
    m = TASK_RE.match(name)
    return f"TASK-{m.group(1)}" if m else None


def next_task_number() -> int:
    """Следующий монотонный номер задачи (сканирует все каталоги handoff)."""
    max_n = 0
    for p, _ in iter_task_files():
        m = TASK_RE.match(p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=check
    )


def in_git_repo() -> bool:
    try:
        r = git("rev-parse", "--is-inside-work-tree", check=False)
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False
