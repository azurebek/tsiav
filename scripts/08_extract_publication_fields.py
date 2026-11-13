#!/usr/bin/env python3
"""Extract auditable publication metadata from provisionally included records.

The output is intentionally publication-level.  Agreement-level consolidation
is a later step because a single agreement can have both a law and a decision.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path


MONTHS = {
    "ocak": 1,
    "subat": 2,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayis": 5,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "agustos": 8,
    "ağustos": 8,
    "eylul": 9,
    "eylül": 9,
    "ekim": 10,
    "kasim": 11,
    "kasım": 11,
    "aralik": 12,
    "aralık": 12,
}

TEXTUAL_DATE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|"
    r"Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)"
    r"\s+(\d{4})\b",
    re.IGNORECASE,
)
NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2})[./](\d{1,2})[./](\d{4})(?!\d)")


def iso_date(day: str, month: str | int, year: str) -> str | None:
    try:
        if isinstance(month, str) and not month.isdigit():
            month_number = MONTHS[month.casefold()]
        else:
            month_number = int(month)
        return date(int(year), month_number, int(day)).isoformat()
    except (KeyError, ValueError):
        return None


def parse_date_match(match: re.Match[str]) -> str | None:
    return iso_date(match.group(1), match.group(2), match.group(3))


def dates_near_signed(text: str) -> list[str]:
    """Return dates directly tied to an imzalan- phrase, in text order."""
    found: list[tuple[int, str]] = []
    for pattern in (TEXTUAL_DATE, NUMERIC_DATE):
        for match in pattern.finditer(text):
            tail = text[match.end() : match.end() + 140]
            # The date must itself be followed by "tarihinde ... imzalan".
            # A loose search can incorrectly attach a nearby law acceptance
            # date to the actual signed-date phrase that follows it.
            if not re.match(r"\s+tarihinde\b.{0,100}\bimzalan", tail, re.IGNORECASE | re.DOTALL):
                continue
            parsed = parse_date_match(match)
            if parsed:
                found.append((match.start(), parsed))
    return list(dict.fromkeys(value for _, value in sorted(found)))


def first_match_date(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    return parse_date_match(match) or ""


def document_numbers(row: dict[str, str], text: str) -> tuple[str, str]:
    law_no = row.get("manual_law_no", "").strip()
    decision_no = row.get("manual_decision_no", "").strip()
    title = row["title_tr"].strip()

    if not law_no:
        match = re.match(r"^(\d{3,5})\s+", title)
        if not match:
            match = re.search(r"\bKanun\s+No\.?\s*[:.]?\s*(\d{3,5})\b", text, re.IGNORECASE)
        if match and "kanun" in title.casefold():
            law_no = match.group(1)

    if not decision_no:
        match = re.match(r"^(\d{4}/\d+)\s+", title)
        if not match:
            match = re.search(
                r"Karar\s+Say[ıi]s[ıi]\s*[:.]?\s*(\d{1,5}(?:/\d+)?)\b",
                f"{title}\n{text}",
                re.IGNORECASE,
            )
        if match:
            decision_no = match.group(1)

    return law_no, decision_no


def approval_date(row: dict[str, str], text: str, law_no: str, decision_no: str) -> tuple[str, str]:
    manual = row.get("manual_date_approved", "").strip()
    if manual:
        return manual, "manual_override"

    if decision_no:
        normalized = re.sub(r"(?<=\d)\s*/\s*(?=\d)", "/", text)
        normalized = re.sub(
            r"(?<!\d)(\d{1,2})/([1-9])(20\d{2})(?!\d)",
            r"\1/\2/\3",
            normalized,
        )
        patterns = (
            re.compile(
                r"Bakanlar\s+Kurulu.{0,20}?nca\s+"
                r"(\d{1,2})[./](\d{1,2})[./](\d{4})\s+tarihinde\s+kararla",
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r"Bakanlar\s+Kurulunca\s+"
                r"(\d{1,2})[./](\d{1,2})[./](\d{4})\s+tarihinde\s+kararla",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        for pattern in patterns:
            parsed = first_match_date(pattern, normalized)
            if parsed:
                return parsed, "cabinet_decision_text"

        cabinet_pattern = re.compile(
            r"Bakanlar\s+Kurulu.{0,35}?"
            r"(\d{1,2})[./](\d{1,2})[./](\d{4})\s+"
            r"tarih\w{0,8}\s+karar",
            re.IGNORECASE | re.DOTALL,
        )
        parsed = first_match_date(cabinet_pattern, normalized)
        if parsed:
            return parsed, "cabinet_decision_text"

        presidential = re.search(r"karar\s+verilmi\w*", normalized, re.IGNORECASE)
        if presidential:
            date_match = TEXTUAL_DATE.search(
                normalized,
                presidential.end(),
                presidential.end() + 160,
            )
            if date_match:
                parsed = parse_date_match(date_match)
                if parsed:
                    return parsed, "presidential_decision_text"

    if law_no:
        pattern = re.compile(
            r"Kabul\s+Tarihi\s*:\s*(\d{1,2})[./](\d{1,2})[./](\d{4})",
            re.IGNORECASE,
        )
        parsed = first_match_date(pattern, text)
        if parsed:
            return parsed, "law_acceptance_text"

    return "", ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, default=Path("data/interim/review_full.csv"))
    parser.add_argument(
        "--extracted",
        type=Path,
        default=Path("data/interim/extracted_docs_full.json"),
    )
    parser.add_argument(
        "--members",
        type=Path,
        default=Path("data/interim/provisional_group_members.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/publication_fields.csv"),
    )
    parser.add_argument(
        "--ocr",
        type=Path,
        default=Path("data/interim/ocr_publication_text.csv"),
    )
    parser.add_argument(
        "--pilot",
        type=Path,
        default=Path("data/final/tsiav_pilot_2017.csv"),
    )
    args = parser.parse_args()

    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        review_rows = list(csv.DictReader(handle))
    extracted_rows = json.loads(args.extracted.read_text(encoding="utf-8"))
    extracted_by_url = {row["source_url"]: row for row in extracted_rows}
    ocr_by_url: dict[str, str] = {}
    if args.ocr.exists():
        with args.ocr.open(encoding="utf-8-sig", newline="") as handle:
            ocr_by_url = {
                item["source_url"]: item["ocr_text"]
                for item in csv.DictReader(handle)
                if item.get("ocr_status") == "ok"
            }
    pilot_by_url: dict[str, dict[str, str]] = {}
    if args.pilot.exists():
        with args.pilot.open(encoding="utf-8-sig", newline="") as handle:
            for item in csv.DictReader(handle):
                for source_url in item["source_url"].split(";"):
                    pilot_by_url[source_url.strip()] = item
    with args.members.open(encoding="utf-8-sig", newline="") as handle:
        member_rows = list(csv.DictReader(handle))
    group_by_candidate = {row["candidate_id"]: row["group_id"] for row in member_rows}

    included = [
        row
        for row in review_rows
        if row["review_status"] == "included" or row["auto_suggestion"] == "include"
    ]
    output_rows: list[dict[str, str]] = []
    for row in included:
        extracted = extracted_by_url.get(row["source_url"], {})
        native_text = extracted.get("text", "")
        ocr_text = ocr_by_url.get(row["source_url"], "")
        # Windows OCR occasionally inserts a space inside a four-digit year
        # (for example, "201 6").  Joining adjacent digits restores the date
        # without guessing missing characters.
        ocr_text = re.sub(r"(?<!\d)(\d{3})\s+(\d)(?!\d)", r"\1\2", ocr_text)
        text = f"{native_text}\n{ocr_text}".strip()
        law_no, decision_no = document_numbers(row, text)
        pilot = pilot_by_url.get(row["source_url"])
        if pilot:
            if row["channel_guess"] == "law" and not law_no:
                law_no = pilot["law_no"]
            if row["channel_guess"] == "decision" and not decision_no:
                decision_no = pilot["decision_no"]

        signed_dates = dates_near_signed(text)
        manual_signed = row.get("manual_date_signed", "").strip()
        pilot_signed = pilot["date_signed"] if pilot else ""
        signed_date = manual_signed or pilot_signed or (max(signed_dates) if signed_dates else "")
        signed_source = (
            "manual_override"
            if manual_signed
            else "pilot_confirmed"
            if pilot_signed
            else "publication_text"
            if signed_date
            else ""
        )
        approved, approved_source = approval_date(row, text, law_no, decision_no)
        if pilot and decision_no and pilot["date_approved"]:
            approved = pilot["date_approved"]
            approved_source = "pilot_confirmed"

        notes: list[str] = []
        if len(signed_dates) > 1:
            notes.append("Multiple signed dates found; later date selected provisionally.")
        if not signed_date:
            notes.append("Signed date not parsed.")
        if not approved:
            notes.append("Approval date not parsed.")
        if not law_no and not decision_no:
            notes.append("Law/decision number not parsed.")

        output_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "group_id": group_by_candidate.get(row["candidate_id"], ""),
                "rg_date": row["rg_date"],
                "channel_guess": row["channel_guess"],
                "title_tr": row["title_tr"],
                "law_no": law_no,
                "decision_no": decision_no,
                "date_signed": signed_date,
                "signed_dates_found": "; ".join(signed_dates),
                "date_signed_source": signed_source,
                "date_approved": approved,
                "date_approved_source": approved_source,
                "extraction_status": (
                    "ocr_augmented" if ocr_text else extracted.get("extraction_status", "missing")
                ),
                "parse_notes": " ".join(notes),
                "source_url": row["source_url"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0])
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    signed_count = sum(bool(row["date_signed"]) for row in output_rows)
    approved_count = sum(bool(row["date_approved"]) for row in output_rows)
    numbered_count = sum(bool(row["law_no"] or row["decision_no"]) for row in output_rows)
    print(f"Wrote {len(output_rows)} publication rows to {args.output}")
    print(f"Signed dates parsed: {signed_count}/{len(output_rows)}")
    print(f"Approval dates parsed: {approved_count}/{len(output_rows)}")
    print(f"Document numbers parsed: {numbered_count}/{len(output_rows)}")


if __name__ == "__main__":
    main()
