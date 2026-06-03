"""
Backup service (M6, TASK-0033, ADR-0009).

Ежечасный бэкап БД (SQLite VACUUM INTO или Postgres pg_dump), ротация 36,
возврат статуса для отправки в админ-канал.
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

from wrbot.config import get_settings

logger = logging.getLogger(__name__)

BACKUPS_DIR = Path("backups")
BACKUP_GLOB = "wrbot-*.sqlite3"
BACKUP_GLOB_PG = "wrbot-*.sql.gz"
KEEP = 36


def ensure_backups_dir() -> None:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


def _parse_sqlite_path(db_url: str) -> str:
    """Extract path from sqlite+aiosqlite:///... url."""
    if "///" in db_url:
        path = db_url.split("///", 1)[1]
        if path.startswith("~"):
            path = str(Path(path).expanduser())
        return path
    return "./data/wrbot.db"


async def _sqlite_backup(db_url: str, ts: str) -> dict[str, Any]:
    ensure_backups_dir()
    src_path = _parse_sqlite_path(db_url)
    backup_file = BACKUPS_DIR / f"wrbot-{ts}.sqlite3"
    try:
        # Use aiosqlite for async vacuum into (online backup)
        async with aiosqlite.connect(src_path) as conn:
            await conn.execute(f"VACUUM INTO '{backup_file}'")
            await conn.commit()
        size = backup_file.stat().st_size if backup_file.exists() else 0
        logger.info("SQLite backup created: %s (%s bytes)", backup_file, size)
        return {"success": True, "file": str(backup_file), "size": size, "error": None}
    except Exception as exc:
        logger.exception("SQLite backup failed")
        if backup_file.exists():
            backup_file.unlink()
        return {"success": False, "file": None, "size": None, "error": str(exc)}


def _pg_backup(db_url: str, ts: str) -> dict[str, Any]:
    ensure_backups_dir()
    backup_file = BACKUPS_DIR / f"wrbot-{ts}.sql.gz"
    try:
        # pg_dump to stdout | gzip
        # timeout 5min
        cmd = [
            "pg_dump",
            db_url,
        ]
        with backup_file.open("wb") as f:
            # use subprocess with gzip
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            gzip_proc = subprocess.Popen(
                ["gzip"],
                stdin=proc.stdout,
                stdout=f,
                stderr=subprocess.PIPE,
            )
            if proc.stdout:
                proc.stdout.close()
            _, err = gzip_proc.communicate(timeout=300)
            if gzip_proc.returncode != 0:
                raise Exception(err.decode() if err else "gzip failed")
            if proc.returncode != 0:
                _, perr = proc.communicate()
                raise Exception(perr.decode() if perr else "pg_dump failed")
        size = backup_file.stat().st_size
        logger.info("PG backup created: %s (%s bytes)", backup_file, size)
        return {"success": True, "file": str(backup_file), "size": size, "error": None}
    except Exception as exc:
        logger.exception("PG backup failed")
        if backup_file.exists():
            backup_file.unlink()
        return {"success": False, "file": None, "size": None, "error": str(exc)}


def create_backup() -> dict[str, Any]:
    """
    Synchronous entry for backup (to run in thread from async job).
    Detects DB type from settings.
    """
    settings = get_settings()
    db_url = settings.database_url
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M")
    if db_url.startswith("sqlite"):
        # run async in sync? use asyncio.run for vacuum
        # but to avoid nested, run sync version
        # for sqlite vacuum, can use sync sqlite3 too, but aiosqlite is fine via run
        return asyncio.run(_sqlite_backup(db_url, ts))
    elif db_url.startswith("postgresql"):
        return _pg_backup(db_url, ts)
    else:
        return {
            "success": False,
            "file": None,
            "size": None,
            "error": f"Unsupported DB: {db_url[:20]}",
        }


def rotate_backups(keep: int = KEEP) -> None:
    """Delete oldest backups, keep last N."""
    ensure_backups_dir()
    sqlite_files = sorted(
        BACKUPS_DIR.glob(BACKUP_GLOB),
        key=lambda p: p.stat().st_mtime,
    )
    pg_files = sorted(
        BACKUPS_DIR.glob(BACKUP_GLOB_PG),
        key=lambda p: p.stat().st_mtime,
    )
    all_files = sorted(sqlite_files + pg_files, key=lambda p: p.stat().st_mtime)
    to_delete = all_files[:-keep] if len(all_files) > keep else []
    for f in to_delete:
        try:
            f.unlink()
            logger.info("Rotated (deleted) old backup: %s", f.name)
        except Exception:
            logger.exception("Failed to delete old backup %s", f)
