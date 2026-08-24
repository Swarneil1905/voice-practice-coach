"""Persistent, atomic allowances for public paid features. No answers or IPs stored."""
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path


def reserve(scope, now=None):
    path = os.getenv("QUOTA_DATABASE")
    if not path:
        return os.getenv("DJANGO_DEBUG", "true").lower() == "true"
    now = time.time() if now is None else now
    date = datetime.fromtimestamp(now, timezone.utc)
    limits = [(date.strftime("%Y-%m"), int(os.getenv(scope.upper() + "_MONTHLY_LIMIT", "10" if scope == "voice" else "100"))),
              (date.strftime("%Y-%m-%d"), int(os.getenv(scope.upper() + "_DAILY_LIMIT", "3" if scope == "voice" else "20")))]
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path, timeout=5, isolation_level=None) as db:
            db.execute("CREATE TABLE IF NOT EXISTS allowance (scope TEXT, period TEXT, used INTEGER NOT NULL, PRIMARY KEY(scope, period))")
            db.execute("CREATE TABLE IF NOT EXISTS voice_lease (expires REAL NOT NULL)")
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM voice_lease WHERE expires <= ?", (now,))
            if scope == "voice" and db.execute("SELECT COUNT(*) FROM voice_lease").fetchone()[0] >= 2:
                db.rollback()
                return False
            for period, limit in limits:
                row = db.execute("SELECT used FROM allowance WHERE scope=? AND period=?", (scope, period)).fetchone()
                if (row[0] if row else 0) >= limit:
                    db.rollback()
                    return False
            for period, _ in limits:
                db.execute("INSERT INTO allowance VALUES (?, ?, 1) ON CONFLICT(scope, period) DO UPDATE SET used=used+1", (scope, period))
            if scope == "voice":
                db.execute("INSERT INTO voice_lease VALUES (?)", (now + 600,))
            db.execute("DELETE FROM allowance WHERE period < ?", (date.strftime("%Y-%m"),))
            db.commit()
        return True
    except (OSError, sqlite3.Error, ValueError):
        return False
