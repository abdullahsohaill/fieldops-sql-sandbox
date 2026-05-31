from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from fieldops.config import get_settings
from fieldops.data.builder import build_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local FieldOps SQLite database.")
    parser.add_argument("--mode", choices=["offline", "refresh"], default="offline")
    parser.add_argument("--db-path", type=Path, default=get_settings().db_path)
    args = parser.parse_args()

    db_path = asyncio.run(build_database(args.db_path, args.mode))
    print(f"Built FieldOps database at {db_path}")


if __name__ == "__main__":
    main()

