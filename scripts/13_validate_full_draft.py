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
ALLOWED_ACTOR_TYPES = {"military", "coast_guard", "gendarmerie", "police"}
ALLOWED_PARTNER_RECOGNITION = {"un_member", "limited"}
ALLOWED_INSTRUMENT_LEVELS = {"intergovernmental", "inter-agency"}


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
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    parser.add_argument("--pilot", type=Path, default=Path("data/final/tsiav_pilot_2017.csv"))
    args = parser.parse_args()

    with args.draft.open(encoding="utf-8-sig", newline="") as handle:
        draft = list(csv.DictReader(handle))
    with args.exceptions.open(encoding="utf-8-sig", newline="") as handle:
        exceptions = list(csv.DictReader(handle))
    with args.core.open(encoding="utf-8-sig", newline="") as handle:
        core = list(csv.DictReader(handle))
    with args.extended.open(encoding="utf-8-sig", newline="") as handle:
        extended = list(csv.DictReader(handle))
    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        review = list(csv.DictReader(handle))
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
        if row["actor_type"] not in ALLOWED_ACTOR_TYPES:
            errors.append(f"{row_id}: invalid actor_type {row['actor_type']!r}")
        if row["partner_recognition"] not in ALLOWED_PARTNER_RECOGNITION:
            errors.append(
                f"{row_id}: invalid partner_recognition {row['partner_recognition']!r}"
            )
        if row["instrument_level"] not in ALLOWED_INSTRUMENT_LEVELS:
            errors.append(f"{row_id}: invalid instrument_level {row['instrument_level']!r}")
        if row["core_sample"] != "true":
            errors.append(f"{row_id}: draft row is not in the core sample")
        if "Provisional row;" in row["notes"]:
            errors.append(f"{row_id}: stale provisional note remains")

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
    draft_pilot_ids = {row["id"] for row in draft if row["id"] in pilot_ids}
    if draft_pilot_ids != pilot_ids:
        errors.append("confirmed pilot IDs in the draft do not exactly match the 2017 fixture")

    exception_statuses = {row["scope_status"] for row in exceptions}
    required_statuses = {"auto_exclude", "extended_only"}
    if not required_statuses.issubset(exception_statuses):
        errors.append("scope exceptions are missing one or more required status classes")
    unresolved = exception_statuses & {"split_required", "needs_user_review"}
    if unresolved:
        errors.append(f"unresolved scope statuses remain: {sorted(unresolved)}")

    draft_ids = {row["id"] for row in draft}
    core_ids = {row["id"] for row in core}
    extended_ids = {row["id"] for row in extended}
    extended_only = [row for row in exceptions if row["scope_status"] == "extended_only"]
    extended_only_ids = {row["id"] for row in extended_only}
    if core_ids != draft_ids:
        errors.append("core dataset IDs do not exactly match the confirmed draft")
    if extended_ids != core_ids | extended_only_ids:
        errors.append("extended dataset does not equal core plus extended-only rows")
    if len(core_ids) != len(core) or len(extended_ids) != len(extended):
        errors.append("duplicate IDs exist in a final dataset")
    if core and extended and list(core[0]) != list(extended[0]):
        errors.append("core and extended datasets have different schemas")
    for row in extended_only:
        if row["core_sample"] != "false":
            errors.append(f"{row['id']}: extended-only row is marked core")
        if row["actor_type"] not in {"coast_guard", "gendarmerie", "police"}:
            errors.append(f"{row['id']}: extended-only actor is not a non-military security force")
        if row["partner_recognition"] not in ALLOWED_PARTNER_RECOGNITION:
            errors.append(f"{row['id']}: invalid extended-only partner recognition")
        if row["instrument_level"] not in ALLOWED_INSTRUMENT_LEVELS:
            errors.append(f"{row['id']}: invalid extended-only instrument level")
        if row["type"] not in ALLOWED_TYPES:
            errors.append(f"{row['id']}: invalid extended-only type")
        if not re.fullmatch(r".+ \([A-Z0-9]{3}\)", row["partner"]):
            errors.append(f"{row['id']}: malformed extended-only partner")
        if not row["source_url"].startswith("https://www.resmigazete.gov.tr/"):
            errors.append(f"{row['id']}: extended-only row lacks an official source")
        parse_iso(row["date_signed"], "date_signed", row["id"], errors)
        if parse_iso(row["date_approved"], "date_approved", row["id"], errors) is None:
            errors.append(f"{row['id']}: extended-only approval date is missing")
    for row in extended:
        if row["actor_type"] in {"coast_guard", "gendarmerie", "police"} and row["core_sample"] != "false":
            errors.append(f"{row['id']}: non-military security-force row entered the core sample")

    unresolved_review = [
        row for row in review if row["review_status"] not in {"included", "excluded"}
    ]
    if unresolved_review:
        errors.append(f"{len(unresolved_review)} publication review rows remain unresolved")
    if not any(row["review_status"] == "included" for row in review):
        errors.append("publication review has no included rows")
    if not any(row["review_status"] == "excluded" for row in review):
        errors.append("publication review has no excluded rows")

    if errors:
        print("Full-draft validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(
        "Full-draft validation passed: "
        f"{len(core)} core rows, {len(extended)} extended rows, {len(exceptions)} exceptions"
    )
    if not any(row["date_in_force"] for row in core):
        warnings.append(
            "date_in_force is not systematically extracted and is blank in all core rows"
        )
    for warning in warnings:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
