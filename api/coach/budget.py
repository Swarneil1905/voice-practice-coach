"""One lifetime budget shared by every paid operation, in integer microdollars."""
import os
import sqlite3
from pathlib import Path

COSTS = {"chat": 50_000, "speech": 100_000, "transcription": 20_000}
LIMIT = 2_000_000
# A conservative allowance for verification before this ledger was installed.
INITIAL_RESERVATION = 200_000


def reserve_cost(operation):
    cost = COSTS.get(operation)
    path = os.getenv("QUOTA_DATABASE")
    if not cost or not path or not Path(path).is_file():
        return False
    try:
        with sqlite3.connect(path, timeout=5, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS lifetime_budget (id INTEGER PRIMARY KEY CHECK(id=1), reserved INTEGER NOT NULL)")
            db.execute("INSERT OR IGNORE INTO lifetime_budget VALUES (1, ?)", (INITIAL_RESERVATION,))
            changed = db.execute("UPDATE lifetime_budget SET reserved=reserved+? WHERE id=1 AND reserved+?<=?", (cost, cost, LIMIT)).rowcount
            db.commit()
            return changed == 1
    except (OSError, sqlite3.Error):
        return False
