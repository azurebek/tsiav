#!/usr/bin/env python3
"""Find plausible under-merged law/decision pairs for manual audit."""

from __future__ import annotations

import argparse
import csv
from difflib import SequenceMatcher
from pathlib import Path


def effective_channel(row: dict[str, str]) -> str:
    folded = row["titles"].casefold()
    if "kanun" in folded and "uygun bulundu" in folded:
        return "law"
    if "onaylanması hakkında karar" in folded or "onaylanmasi hakkinda karar" in folded:
        return "decision"
    return row["channels"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--groups",
        type=Path,
        default=Path("data/interim/provisional_agreement_groups.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/dedup_merge_candidates.csv"),
    )
    parser.add_argument("--threshold", type=float, default=0.72)
    args = parser.parse_args()

    with args.groups.open(encoding="utf-8-sig", newline="") as handle:
        groups = list(csv.DictReader(handle))

    singletons = [row for row in groups if row["publication_count"] == "1"]
    candidates: list[dict[str, str]] = []
    for index, left in enumerate(singletons):
        left_channel = effective_channel(left)
        left_year = int(left["rg_dates"][:4])
        for right in singletons[index + 1 :]:
            right_channel = effective_channel(right)
            if {left_channel, right_channel} != {"law", "decision"}:
                continue
            right_year = int(right["rg_dates"][:4])
            if abs(left_year - right_year) > 5:
                continue

            similarity = SequenceMatcher(
                None, left["canonical_key"], right["canonical_key"]
            ).ratio()
            if similarity < args.threshold:
                continue
            candidates.append(
                {
                    "similarity": f"{similarity:.4f}",
                    "left_group_id": left["group_id"],
                    "left_channel": left_channel,
                    "left_rg_date": left["rg_dates"],
                    "left_title": left["titles"],
                    "right_group_id": right["group_id"],
                    "right_channel": right_channel,
                    "right_rg_date": right["rg_dates"],
                    "right_title": right["titles"],
                }
            )

    candidates.sort(key=lambda row: float(row["similarity"]), reverse=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "similarity",
        "left_group_id",
        "left_channel",
        "left_rg_date",
        "left_title",
        "right_group_id",
        "right_channel",
        "right_rg_date",
        "right_title",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    print(f"Wrote {len(candidates)} merge candidates to {args.output}")


if __name__ == "__main__":
    main()
