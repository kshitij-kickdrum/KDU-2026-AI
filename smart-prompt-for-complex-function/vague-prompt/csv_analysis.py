from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Union


TRUE_VALUES = {"true", "1", "yes", "y", "active"}


def average_revenue_by_category(
    csv_path: Union[str, Path],
) -> List[Dict[str, float]]:
    """Read a CSV, keep active rows, group by category, and sort by average revenue.

    Expected columns: ``active``, ``category``, and ``revenue``.
    Rows are treated as active when ``active`` is one of: true, 1, yes, y, active.
    """

    totals = defaultdict(float)
    counts = defaultdict(int)

    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        required_columns = {"active", "category", "revenue"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            missing = required_columns.difference(reader.fieldnames or [])
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for row in reader:
            is_active = str(row["active"]).strip().lower() in TRUE_VALUES
            if not is_active:
                continue

            category = str(row["category"]).strip()
            if not category:
                continue

            revenue = float(row["revenue"])
            totals[category] += revenue
            counts[category] += 1

    result = [
        {"category": category, "average_revenue": totals[category] / counts[category]}
        for category in totals
    ]

    return sorted(
        result,
        key=lambda item: (-item["average_revenue"], item["category"]),
    )
