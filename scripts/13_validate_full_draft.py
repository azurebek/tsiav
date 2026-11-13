#!/usr/bin/env python3
"""Validate structural and semantic invariants of the current full-run draft."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from datetime import date
from pathlib import Path


ALLOWED_TYPES = {
    "training",
    "framework",
    "defence_industry",
    "protocol_amendment",
    "military_financial",
    "other_military",
}


def split_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def fold_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks.replace("ı", "i")


def parse_iso(value: str, label: str, row_id: str, errors: list[str]) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{row_id}: invalid {label}={value!r}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--draft",
        type=Path,
        default=Path("data/interim/dataset_draft.csv"),
    )
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=Path("data/interim/scope_exceptions.csv"),
    )
    parser.add_argument("--pilot", type=Path, default=Path("data/final/tsiav_pilot_2017.csv"))
    args = parser.parse_args()

    with args.draft.open(encoding="utf-8-sig", newline="") as handle:
        draft = list(csv.DictReader(handle))
    with args.exceptions.open(encoding="utf-8-sig", newline="") as handle:
        exceptions = list(csv.DictReader(handle))
    with args.pilot.open(encoding="utf-8-sig", newline="") as handle:
        pilot = list(csv.DictReader(handle))

    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    for row in draft:
        row_id = row["id"]
        if row_id in ids:
            errors.append(f"duplicate id: {row_id}")
        ids.add(row_id)

        if row["scope_status"] not in {"confirmed_in", "provisional_in"}:
            errors.append(f"{row_id}: non-draft scope status {row['scope_status']}")
        if row["type"] not in ALLOWED_TYPES:
            errors.append(f"{row_id}: invalid type {row['type']!r}")

        expected_framework = "cerceve" in fold_for_match(row["title_tr"])
        if (row["is_framework"] == "true") != expected_framework:
            errors.append(f"{row_id}: is_framework does not match title")

        if not re.fullmatch(r".+ \([A-Z0-9]{3}\)", row["partner"]):
            errors.append(f"{row_id}: missing or malformed partner {row['partner']!r}")
        if re.search(r"Onaylanmas|Yürürlüğe Girmesi|Karar Sayısı", row["title_tr"], re.IGNORECASE):
            errors.append(f"{row_id}: title still contains publication wrapper text")
        if re.match(r"^[–—-]", row["title_tr"]):
            errors.append(f"{row_id}: title starts with an index dash")

        sources = split_values(row["source_url"])
        rg_dates = split_values(row["rg_date"])
        rg_issues = split_values(row["rg_issue"])
        if not sources or any(not url.startswith("https://www.resmigazete.gov.tr/") for url in sources):
            errors.append(f"{row_id}: missing or non-official source URL")
        if not (len(sources) == len(rg_dates) == len(rg_issues)):
            errors.append(
                f"{row_id}: source/date/issue counts differ "
                f"({len(sources)}/{len(rg_dates)}/{len(rg_issues)})"
            )

        signed = parse_iso(row["date_signed"], "date_signed", row_id, errors)
        approved = parse_iso(row["date_approved"], "date_approved", row_id, errors)
        publication_dates = [parse_iso(value, "rg_date", row_id, errors) for value in rg_dates]
        publication_dates = [value for value in publication_dates if value]
        if approved is None:
            errors.append(f"{row_id}: approval date is missing")
        if signed is None:
            warnings.append(f"{row_id}: signed date is missing")
        if signed and approved and signed > approved:
            errors.append(f"{row_id}: signed date is after approval date")
        if approved and publication_dates and approved > max(publication_dates):
            errors.append(f"{row_id}: approval date is after publication date")

        if row["channel"] == "both" and not (row["law_no"] and row["decision_no"]):
            errors.append(f"{row_id}: channel=both without both document numbers")
        if row["channel"] == "law" and not row["law_no"]:
            errors.append(f"{row_id}: law channel without law number")
        if row["channel"] == "decision" and not row["decision_no"]:
            errors.append(f"{row_id}: decision channel without decision number")

    pilot_ids = {row["id"] for row in pilot}
    draft_pilot_ids = {row["id"] for row in draft if row["status"] == "included"}
    if draft_pilot_ids != pilot_ids:
        errors.append("confirmed pilot IDs in the draft do not exactly match the 2017 fixture")

    exception_statuses = {row["scope_status"] for row in exceptions}
    required_statuses = {"auto_exclude", "split_required", "needs_user_review"}
    if not required_statuses.issubset(exception_statuses):
        errors.append("scope exceptions are missing one or more required status classes")

    if errors:
        print("Full-draft validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Full-draft validation passed: {len(draft)} draft rows, {len(exceptions)} exceptions")
    for warning in warnings:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
