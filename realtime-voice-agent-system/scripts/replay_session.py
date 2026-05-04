from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from monitoring.monitor import Monitor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("session_id")
    args = parser.parse_args()
    settings = Settings.load(require_api_keys=False)
    monitor = Monitor(settings.log_file_path)
    for event in monitor.replay(args.session_id):
        print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()

