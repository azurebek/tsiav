#!/usr/bin/env python3
"""Regression-check provisional grouping and parsed fields against the 2017 pilot."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def split_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=Path("data/final/tsiav_pilot_2017.csv"))
    parser.add_argument(
        "--fields",
        type=Path,
        default=Path("data/interim/publication_fields.csv"),
    )
    parser.add_argument(
        "--groups",
        type=Path,
        default=Path("tmp/groups_2017.csv"),
    )
    args = parser.parse_args()

    with args.pilot.open(encoding="utf-8-sig", newline="") as handle:
        pilot = list(csv.DictReader(handle))
    with args.fields.open(encoding="utf-8-sig", newline="") as handle:
        fields = list(csv.DictReader(handle))
    with args.groups.open(encoding="utf-8-sig", newline="") as handle:
        groups = list(csv.DictReader(handle))

    by_url = {row["source_url"]: row for row in fields}
    errors: list[str] = []
    if len(groups) != len(pilot):
        errors.append(f"2017 groups={len(groups)} but pilot agreements={len(pilot)}")

    for expected in pilot:
        publications = [by_url.get(url) for url in split_values(expected["source_url"])]
        if any(row is None for row in publications):
            errors.append(f"{expected['id']}: one or more source URLs missing from publication fields")
            continue

        signed = {row["date_signed"] for row in publications if row["date_signed"]}
        approvals = {
            row["date_approved"]
            for row in publications
            if row["decision_no"] and row["date_approved"]
        }
        laws = {row["law_no"] for row in publications if row["law_no"]}
        decisions = {row["decision_no"] for row in publications if row["decision_no"]}

        if expected["date_signed"] not in signed:
            errors.append(f"{expected['id']}: signed date mismatch ({sorted(signed)})")
        if expected["law_no"] and expected["law_no"] not in laws:
            errors.append(f"{expected['id']}: law number mismatch ({sorted(laws)})")
        if expected["decision_no"] and expected["decision_no"] not in decisions:
            errors.append(f"{expected['id']}: decision number mismatch ({sorted(decisions)})")
        if expected["decision_no"] and expected["date_approved"] not in approvals:
            errors.append(f"{expected['id']}: approval date mismatch ({sorted(approvals)})")

    if errors:
        print("Pilot regression failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    publication_count = sum(len(split_values(row["source_url"])) for row in pilot)
    print(f"Pilot regression passed: {len(pilot)} agreements, {publication_count} publications")


if __name__ == "__main__":
    main()
