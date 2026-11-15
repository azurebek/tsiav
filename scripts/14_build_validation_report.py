#!/usr/bin/env python3
"""Build a deterministic Markdown validation report for the final datasets."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter
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
NON_MILITARY_ACTORS = {"coast_guard", "gendarmerie", "police"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def markdown_table(headers: list[str], rows: list[list[str | int]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, default=Path("data/final/tsiav_2010_2026.csv"))
    parser.add_argument(
        "--extended",
        type=Path,
        default=Path("data/final/tsiav_2010_2026_extended.csv"),
    )
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=Path("data/interim/scope_exceptions.csv"),
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("VALIDATION_REPORT.md"))
    parser.add_argument("--snapshot", default="2026-11-13")
    args = parser.parse_args()

    core = read_csv(args.core)
    extended = read_csv(args.extended)
    exceptions = read_csv(args.exceptions)
    review = read_csv(args.review)

    errors: list[str] = []
    warnings: list[str] = []
    core_ids = [row["id"] for row in core]
    extended_ids = [row["id"] for row in extended]
    extended_only = [row for row in extended if row["core_sample"] == "false"]

    if len(core_ids) != len(set(core_ids)):
        errors.append("core dataset contains duplicate IDs")
    if len(extended_ids) != len(set(extended_ids)):
        errors.append("extended dataset contains duplicate IDs")
    if core and extended and list(core[0]) != list(extended[0]):
        errors.append("core and extended schemas differ")
    if set(extended_ids) != set(core_ids) | {row["id"] for row in extended_only}:
        errors.append("extended dataset is not exactly core plus extended-only rows")
    if any(row["core_sample"] != "true" for row in core):
        errors.append("one or more core rows have core_sample != true")
    if any(row["scope_status"] != "confirmed_in" for row in core):
        errors.append("one or more core rows are not confirmed_in")
    if any(row["status"] != "included" for row in extended):
        errors.append("one or more released rows are not marked included")

    for row in extended:
        row_id = row["id"]
        if row["type"] not in ALLOWED_TYPES:
            errors.append(f"{row_id}: invalid type {row['type']!r}")
        if not re.fullmatch(r".+ \([A-Z0-9]{3}\)", row["partner"]):
            errors.append(f"{row_id}: malformed partner {row['partner']!r}")
        expected_framework = "cerceve" in fold_for_match(row["title_tr"])
        if (row["is_framework"] == "true") != expected_framework:
            errors.append(f"{row_id}: is_framework does not match title")

        sources = split_values(row["source_url"])
        rg_dates = split_values(row["rg_date"])
        rg_issues = split_values(row["rg_issue"])
        if not sources or any(
            not source.startswith("https://www.resmigazete.gov.tr/") for source in sources
        ):
            errors.append(f"{row_id}: missing or non-official source URL")
        if not (len(sources) == len(rg_dates) == len(rg_issues)):
            errors.append(f"{row_id}: source/date/issue counts differ")

        signed = parse_iso(row["date_signed"], "date_signed", row_id, errors)
        approved = parse_iso(row["date_approved"], "date_approved", row_id, errors)
        publications = [parse_iso(value, "rg_date", row_id, errors) for value in rg_dates]
        publications = [value for value in publications if value]
        if approved is None:
            errors.append(f"{row_id}: approval date is missing")
        if signed is None:
            warnings.append(f"{row_id}: signed date is missing")
        if signed and approved and signed > approved:
            errors.append(f"{row_id}: signed date is after approval date")
        if approved and publications and approved > max(publications):
            errors.append(f"{row_id}: approval date is after publication date")
        if row["actor_type"] in NON_MILITARY_ACTORS and row["core_sample"] != "false":
            errors.append(f"{row_id}: non-military security actor entered the core sample")

    exception_counts = Counter(row["scope_status"] for row in exceptions)
    if exception_counts.get("needs_user_review") or exception_counts.get("split_required"):
        errors.append("unresolved scope decisions remain")

    if errors:
        print("Validation report failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    type_counts = Counter(row["type"] for row in core)
    approval_years = Counter(row["date_approved"][:4] for row in core)
    partner_counts = Counter(row["partner"] for row in core)
    channel_counts = Counter(row["channel"] for row in core)
    instrument_counts = Counter(row["instrument_level"] for row in core)
    source_refs = [source for row in core for source in split_values(row["source_url"])]
    missing_signed = [row for row in core if not row["date_signed"]]

    lines: list[str] = [
        "# TSİAV 2010–2026 validation report",
        "",
        f"Snapshot: `{args.snapshot}`",
        "",
        "## Release summary",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Measure", "Result"],
            [
                ["Core agreement rows", len(core)],
                ["Extended agreement rows", len(extended)],
                ["Extended-only rows", len(extended_only)],
                ["Core partner entities", len(partner_counts)],
                ["Candidate publication URLs reviewed", len(review)],
                ["Core official-source references", len(source_refs)],
                ["Unique core official-source URLs", len(set(source_refs))],
                ["Core rows with signed date", len(core) - len(missing_signed)],
                ["Core rows with approval date", sum(bool(row["date_approved"]) for row in core)],
                ["Core framework-title rows", sum(row["is_framework"] == "true" for row in core)],
            ],
        )
    )
    lines.extend(["", "## Automated checks", ""])
    checks = [
        "Unique IDs in both release files",
        "Identical core and extended schemas",
        "Extended release equals core plus extended-only records",
        "All core rows are confirmed and marked `core_sample = true`",
        "Every released row has an official Resmî Gazete URL",
        "Source URL, issue, and publication-date list lengths align",
        "All approval dates are present and chronologically valid",
        "`is_framework` exactly matches `çerçeve` in the official title",
        "Non-military security-force records do not enter the core sample",
        "No unresolved split or user-review status remains",
    ]
    lines.extend(f"- PASS — {check}" for check in checks)

    lines.extend(["", "## Known data limitation", ""])
    if missing_signed:
        for row in missing_signed:
            lines.append(
                f"- `{row['id']}` ({row['partner']}): `date_signed` is blank; "
                "the official approval and publication fields are complete."
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Core distribution by type", ""])
    lines.extend(
        markdown_table(
            ["Type", "Rows"],
            [[key, type_counts[key]] for key in sorted(type_counts)],
        )
    )
    lines.extend(["", "## Core distribution by approval year", ""])
    lines.extend(
        markdown_table(
            ["Approval year", "Rows"],
            [[key, approval_years[key]] for key in sorted(approval_years)],
        )
    )
    lines.extend(["", "## Core distribution by publication channel", ""])
    lines.extend(
        markdown_table(
            ["Channel", "Rows"],
            [[key, channel_counts[key]] for key in sorted(channel_counts)],
        )
    )
    lines.extend(["", "## Core distribution by instrument level", ""])
    lines.extend(
        markdown_table(
            ["Instrument level", "Rows"],
            [[key, instrument_counts[key]] for key in sorted(instrument_counts)],
        )
    )
    lines.extend(["", "## Core partner coverage", ""])
    lines.extend(
        markdown_table(
            ["Partner", "Rows"],
            [[key, partner_counts[key]] for key in sorted(partner_counts)],
        )
    )
    lines.extend(["", "## Extended-only records", ""])
    if extended_only:
        lines.extend(
            markdown_table(
                ["ID", "Partner", "Actor type", "Recognition", "Instrument level"],
                [
                    [
                        row["id"],
                        row["partner"],
                        row["actor_type"],
                        row["partner_recognition"],
                        row["instrument_level"],
                    ]
                    for row in extended_only
                ],
            )
        )
    else:
        lines.append("No extended-only records.")

    lines.extend(["", "## Scope-exception disposition", ""])
    lines.extend(
        markdown_table(
            ["Scope status", "Rows"],
            [[key, exception_counts[key]] for key in sorted(exception_counts)],
        )
    )
    lines.extend(
        [
            "",
            "The report is generated by `scripts/14_build_validation_report.py`; "
            "manual edits to this file will be overwritten.",
            "",
        ]
    )

    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validation report passed: {len(core)} core rows, "
        f"{len(extended)} extended rows, {len(warnings)} warning(s) -> {args.output}"
    )


if __name__ == "__main__":
    main()
