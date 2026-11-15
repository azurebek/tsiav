#!/usr/bin/env python3
"""Cross-platform runner for the cached full-corpus processing stage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ["scripts/05_prepare_review.py"],
    ["scripts/06_deduplicate.py"],
    ["scripts/07_audit_dedup.py", "--threshold", "0.72"],
    ["scripts/08_extract_publication_fields.py"],
    ["scripts/09_ocr_missing_publications.py"],
    ["scripts/08_extract_publication_fields.py"],
    [
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
    ["scripts/10_validate_pilot.py"],
    ["scripts/11_build_provisional_dataset.py"],
    ["scripts/12_finalize_publication_review.py"],
    ["scripts/12_materialize_review_outputs.py"],
    ["scripts/13_validate_full_draft.py"],
    ["scripts/14_build_validation_report.py"],
]


def main() -> None:
    for arguments in STEPS:
        command = [sys.executable, *arguments]
        print("===", " ".join(command), "===", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
