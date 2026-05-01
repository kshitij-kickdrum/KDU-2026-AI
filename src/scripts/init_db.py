from __future__ import annotations

from src.storage.database import Database
from src.utils.config import load_config


def main() -> None:
    config = load_config()
    database = Database(config.database_path)
    database.initialize()
    print(f"Initialized database at {config.database_path}")


if __name__ == "__main__":
    main()
