from pathlib import Path

from csv_analysis import average_revenue_by_category


def test_average_revenue_by_category(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "\n".join(
            [
                "active,category,revenue",
                "true,A,100",
                "false,A,500",
                "yes,B,200",
                "1,A,300",
                "active,B,100",
            ]
        ),
        encoding="utf-8",
    )

    assert average_revenue_by_category(csv_file) == [
        {"category": "A", "average_revenue": 200.0},
        {"category": "B", "average_revenue": 150.0},
    ]
