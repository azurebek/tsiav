#!/usr/bin/env python3
"""Group likely law/decision publications into provisional agreement records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def fold_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks.replace("ı", "i")


def canonical_title(title: str) -> str:
    value = fold_for_match(title)
    value = re.sub(r"^[\W_]+", "", value)
    value = re.sub(r"^(?:\d{4}/\d+|\d{3,5})\s+", "", value)
    value = re.sub(r"\s*\(karar (?:sayisi|no):.*\)\s*$", "", value)

    approval_markers = (
        " onaylanmasinin uygun bulunduguna dair kanun",
        " onaylanmasinin uygun bulundugu hakkinda kanun",
        " onaylanmasi hakkinda karar",
        " onaylanmasi hakkinda",
        " yururluge girmesi hakkinda karar",
        " yururluge girmesi hakkinda",
    )
    marker_positions = [value.find(marker) for marker in approval_markers if marker in value]
    if marker_positions:
        value = value[: min(marker_positions)]

    value = re.sub(r"\s+(?:ilisik\s+)?notalarla birlikte$", "", value)
    value = re.sub(r"\barasindaki\b", "arasinda", value)
    value = re.sub(r"\barasinda imzalanan\b", "arasinda", value)
    # Correct a known Resmi Gazete index typo in the 2010 Slovak agreement.
    value = value.replace("slovak cumhuriyete hukumeti", "slovak cumhuriyeti hukumeti")
    # Turkish approval titles often attach the possessive suffix after a
    # straight or curly apostrophe (for example, "Anlaşması'nın").  Remove
    # punctuation before normalising terminal forms so law and decision
    # publications produce the same agreement key.
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    terminal_forms = {
        "anlasmasinin": "anlasmasi",
        "anlasmasi nin": "anlasmasi",
        "muhtirasinin": "muhtirasi",
        "muhtirasi nin": "muhtirasi",
        "protokolunun": "protokolu",
        "protokolu nun": "protokolu",
        "duzenlemenin": "duzenleme",
        "notunun": "notu",
        "notu nun": "notu",
    }
    for source, replacement in terminal_forms.items():
        value = re.sub(rf"\b{source}$", replacement, value)

    return re.sub(r"[^a-z0-9]+", "", value)


def split_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def unique_join(values: list[str]) -> str:
    return "; ".join(dict.fromkeys(item for item in values if item))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    parser.add_argument(
        "--groups",
        type=Path,
        default=Path("data/interim/provisional_agreement_groups.csv"),
    )
    parser.add_argument(
        "--members",
        type=Path,
        default=Path("data/interim/provisional_group_members.csv"),
    )
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    args = parser.parse_args()

    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if args.start_year is not None:
        rows = [row for row in rows if int(row["rg_date"][:4]) >= args.start_year]
    if args.end_year is not None:
        rows = [row for row in rows if int(row["rg_date"][:4]) <= args.end_year]

    included = [
        row
        for row in rows
        if row["review_status"] == "included" or row["auto_suggestion"] == "include"
    ]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in included:
        key = canonical_title(row["title_tr"])
        if not key:
            raise ValueError(f"Empty canonical title for {row['source_url']}")
        grouped[key].append(row)

    group_rows: list[dict[str, str]] = []
    member_rows: list[dict[str, str]] = []
    for key, members in sorted(grouped.items(), key=lambda item: min(row["rg_date"] for row in item[1])):
        group_id = "GRP-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        channels = [row["channel_guess"] for row in members]
        types = [row["manual_type"] or row["suggested_type"] for row in members]
        framework_values = [row["is_framework"] for row in members]
        statuses = [row["review_status"] for row in members]

        group_rows.append(
            {
                "group_id": group_id,
                "canonical_key": key,
                "publication_count": str(len(members)),
                "channels": unique_join(channels),
                "rg_dates": unique_join([row["rg_date"] for row in members]),
                "rg_issues": unique_join([row["rg_issue"] for row in members]),
                "source_urls": unique_join([row["source_url"] for row in members]),
                "titles": unique_join([row["title_tr"] for row in members]),
                "suggested_types": unique_join(types),
                "is_framework": "true" if "true" in framework_values else "false",
                "review_state": (
                    "confirmed" if all(status in {"included", "excluded"} for status in statuses) else "provisional"
                ),
            }
        )

        for row in members:
            member_rows.append(
                {
                    "group_id": group_id,
                    "candidate_id": row["candidate_id"],
                    "rg_date": row["rg_date"],
                    "channel_guess": row["channel_guess"],
                    "title_tr": row["title_tr"],
                    "source_url": row["source_url"],
                    "review_status": row["review_status"],
                    "auto_suggestion": row["auto_suggestion"],
                }
            )

    args.groups.parent.mkdir(parents=True, exist_ok=True)
    with args.groups.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(group_rows[0]))
        writer.writeheader()
        writer.writerows(group_rows)

    with args.members.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(member_rows[0]))
        writer.writeheader()
        writer.writerows(member_rows)

    print(f"Grouped {len(included)} publications into {len(group_rows)} provisional agreements")
    print(f"Wrote groups to {args.groups}")
    print(f"Wrote members to {args.members}")


if __name__ == "__main__":
    main()
