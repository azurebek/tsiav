#!/usr/bin/env python3
"""Cross-platform runner for the resumable collection stage."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    command = [sys.executable, *arguments]
    print("===", " ".join(command), "===", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--through", required=True)
    parser.add_argument("--delay", type=float, default=2.3)
    args = parser.parse_args()

    for year in range(args.start_year, args.end_year + 1):
        run(
            "scripts/01_download_index.py",
            "--year",
            str(year),
            "--through",
            args.through,
            "--delay",
            str(args.delay),
        )
    run(
        "scripts/02_filter.py",
        "--start-year",
        str(args.start_year),
        "--end-year",
        str(args.end_year),
        "--output",
        "data/interim/candidates_full.csv",
    )
    run(
        "scripts/03_fetch_docs.py",
        "--input",
        "data/interim/candidates_full.csv",
        "--output",
        "data/raw/docs",
        "--failures",
        "data/interim/download_failures.csv",
        "--delay",
        str(args.delay),
    )
    run(
        "scripts/04_extract.py",
        "--candidates",
        "data/interim/candidates_full.csv",
        "--docs",
        "data/raw/docs",
        "--output",
        "data/interim/extracted_docs_full.json",
    )


if __name__ == "__main__":
    main()
