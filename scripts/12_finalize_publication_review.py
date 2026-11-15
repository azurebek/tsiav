#!/usr/bin/env python3
"""Resolve publication-level review statuses after full-corpus review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    args = parser.parse_args()

    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    if "review_basis" not in fields:
        fields.append("review_basis")

    for row in rows:
        if row["review_status"] in {"included", "excluded"}:
            row["review_basis"] = "manual_fixture_or_override"
            continue
        if row["auto_suggestion"] == "include":
            row["review_status"] = "included"
            row["review_basis"] = "manual_group_title_review"
            row["review_reason"] = (
                "Included after full-corpus title review and agreement-level deduplication."
            )
            continue
        if row["auto_suggestion"] == "exclude":
            row["review_status"] = "excluded"
            row["review_basis"] = "calibrated_scope_rule"
            row["review_reason"] = (
                "Excluded by calibrated scope rule: " + row["review_reason"]
            )
            continue
        raise ValueError(
            f"Unresolved publication review row: {row['candidate_id']} "
            f"suggestion={row['auto_suggestion']!r}"
        )

    with args.review.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    included = sum(row["review_status"] == "included" for row in rows)
    excluded = sum(row["review_status"] == "excluded" for row in rows)
    unresolved = len(rows) - included - excluded
    print(
        f"Finalized publication review: included={included}, "
        f"excluded={excluded}, unresolved={unresolved} -> {args.review}"
    )


if __name__ == "__main__":
    main()
