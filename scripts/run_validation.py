#!/usr/bin/env python3
"""Run the release tests and committed-artifact validators."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [
        sys.executable,
        "scripts/06_deduplicate.py",
        "--start-year",
        "2017",
        "--end-year",
        "2017",
        "--groups",
        "tmp/groups_2017.csv",
        "--members",
        "tmp/members_2017.csv",
    ],
    [sys.executable, "scripts/10_validate_pilot.py"],
    [sys.executable, "scripts/13_validate_full_draft.py"],
    [sys.executable, "scripts/14_build_validation_report.py"],
]


def main() -> None:
    for command in COMMANDS:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
