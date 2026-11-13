#!/usr/bin/env python3
"""Materialize review artifacts plus the core and extended final datasets."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/interim/provisional_dataset.csv"),
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    parser.add_argument(
        "--draft",
        type=Path,
        default=Path("data/interim/dataset_draft.csv"),
    )
    parser.add_argument(
        "--scope-exceptions",
        type=Path,
        default=Path("data/interim/scope_exceptions.csv"),
    )
    parser.add_argument(
        "--exclusion-log",
        type=Path,
        default=Path("data/interim/exclusion_log.csv"),
    )
    parser.add_argument(
        "--core",
        type=Path,
        default=Path("data/final/tsiav_2010_2026.csv"),
    )
    parser.add_argument(
        "--extended",
        type=Path,
        default=Path("data/final/tsiav_2010_2026_extended.csv"),
    )
    args = parser.parse_args()

    with args.dataset.open(encoding="utf-8-sig", newline="") as handle:
        dataset = list(csv.DictReader(handle))
    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        review = list(csv.DictReader(handle))

    draft = [
        row
        for row in dataset
        if row["scope_status"] in {"confirmed_in", "provisional_in"}
    ]
    exceptions = [
        row
        for row in dataset
        if row["scope_status"] not in {"confirmed_in", "provisional_in"}
    ]
    core = [row for row in dataset if row["core_sample"] == "true"]
    extended = [
        row
        for row in dataset
        if row["core_sample"] == "true" or row["scope_status"] == "extended_only"
    ]
    exclusions = [
        {
            "candidate_id": row["candidate_id"],
            "rg_date": row["rg_date"],
            "rg_issue": row["rg_issue"],
            "title_tr": row["title_tr"],
            "source_url": row["source_url"],
            "exclusion_status": (
                "confirmed_excluded"
                if row["review_status"] == "excluded"
                else "auto_exclude_provisional"
            ),
            "reason": row["review_reason"],
        }
        for row in review
        if row["review_status"] == "excluded" or row["auto_suggestion"] == "exclude"
    ]

    write_csv(args.draft, draft, list(dataset[0]))
    write_csv(args.scope_exceptions, exceptions, list(dataset[0]))
    write_csv(args.core, core, list(dataset[0]))
    write_csv(args.extended, extended, list(dataset[0]))
    write_csv(
        args.exclusion_log,
        exclusions,
        [
            "candidate_id",
            "rg_date",
            "rg_issue",
            "title_tr",
            "source_url",
            "exclusion_status",
            "reason",
        ],
    )

    print(f"Draft agreements: {len(draft)} -> {args.draft}")
    print(f"Scope exceptions: {len(exceptions)} -> {args.scope_exceptions}")
    print(f"Core dataset: {len(core)} -> {args.core}")
    print(f"Extended dataset: {len(extended)} -> {args.extended}")
    print(f"Publication exclusions: {len(exclusions)} -> {args.exclusion_log}")


if __name__ == "__main__":
    main()
