from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from storage.sqlite_store import SQLiteStore


ROWS = [
    ("C-00123", "Asha Patel", "asha@example.com", "Pro", 42.50, "2026-05-20", "current", "2026-01-01T00:00:00Z"),
    ("C-00456", "Ravi Kumar", "ravi@example.com", "Starter", 18.00, "2026-05-10", "overdue", "2026-01-08T00:00:00Z"),
    ("C-00789", "Maya Singh", "maya@example.com", "Enterprise", 0.00, "2026-06-01", "current", "2026-02-02T00:00:00Z"),
]


def main() -> None:
    settings = Settings.load(require_api_keys=False)
    store = SQLiteStore(settings.sqlite_db_path)
    store.initialize()
    for row in ROWS:
        store.execute(
            """
            INSERT OR REPLACE INTO customer_billing
            (customer_id, full_name, email, plan_name, balance_usd, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
    print(f"Seeded {len(ROWS)} customer rows into {settings.sqlite_db_path}")


if __name__ == "__main__":
    main()

