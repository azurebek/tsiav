#!/usr/bin/env python3
"""Prepare a conservative full-run review queue without making final judgments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXCLUSION_RULES = [
    (
        (
            "yurt dışına gönderilmesi",
            "yabancı ülkelere gönderilmesi",
            "unifil",
            "harekâtına iştirak",
            "harekatına iştirak",
            "izin süresinin",
            "izin verilmesine dair karar",
        ),
        "Military deployment mandate rather than a bilateral cooperation agreement.",
    ),
    (
        (
            "atama kararı",
            "atama kararları",
            "vekâlet etmesine",
            "vekalet etmesine",
            "görevden alınması",
        ),
        "Domestic personnel appointment or acting-minister notice.",
    ),
    (
        (
            "yönetmeliği",
            "yönetmelik",
            "disiplin amirleri",
            "görevde yükselme",
            "unvan değişikliği",
        ),
        "Domestic regulation rather than a bilateral agreement.",
    ),
    (
        (
            "askeri yüksek idare mahkemesi",
            "askerî yüksek idare mahkemesi",
            "askeri yargıtay",
            "askerî yargıtay",
            "komisyon kararı",
        ),
        "Domestic court or commission decision.",
    ),
    (
        (
            "kontrole tâbi tutulacak harp araç",
            "kontrole tabi tutulacak harp araç",
            "kontrole tabi malzeme listesi",
        ),
        "Domestic controlled-material list.",
    ),
]

INSTRUMENT_TERMS = ("anlaşma", "mutabakat muhtırası", "protokol")
DEFENCE_TERMS = ("asker", "savunma", "silahlı kuvvet", "harp", "lojistik")
BILATERAL_MARKERS = (
    "hükümeti ile",
    "bakanlığı ile",
    "başkanlığı ile",
    "kuvvetleri ile",
    "cumhuriyeti ile",
    "devleti ile",
)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def suggest_status(title: str) -> tuple[str, str]:
    folded = title.casefold()
    for phrases, reason in EXCLUSION_RULES:
        if any(phrase in folded for phrase in phrases):
            return "exclude", reason

    has_instrument = any(term in folded for term in INSTRUMENT_TERMS)
    has_defence_scope = any(term in folded for term in DEFENCE_TERMS)
    looks_bilateral = any(marker in folded for marker in BILATERAL_MARKERS)
    if has_instrument and has_defence_scope and looks_bilateral:
        return "include", "Title looks like a bilateral defence cooperation instrument."

    return "needs_review", "Title alone is not decisive under the conservative rules."


def suggest_type(title: str) -> str:
    folded = title.casefold()
    if "protokol" in folded or "değişiklik" in folded:
        return "protocol_amendment"
    if any(term in folded for term in ("askerî mali", "askeri mali", "nakdi yardım", "mali iş birliği", "mali işbirliği")):
        return "military_financial"
    if "savunma sanayi" in folded:
        return "defence_industry"
    if "eğitim" in folded and any(term in folded for term in ("asker", "teknik", "bilimsel")):
        return "training"
    if any(term in folded for term in ("askerî iş birliği", "askeri iş birliği", "askerî işbirliği", "askeri işbirliği")):
        return "framework"
    if any(term in folded for term in DEFENCE_TERMS):
        return "other_military"
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--extracted",
        type=Path,
        default=Path("data/interim/extracted_docs_full.json"),
    )
    parser.add_argument(
        "--pilot-review",
        type=Path,
        default=Path("data/interim/review.csv"),
    )
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path("data/interim/manual_extraction_overrides.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    args = parser.parse_args()

    records = json.loads(args.extracted.read_text(encoding="utf-8"))
    pilot_by_url = {row["source_url"]: row for row in load_csv(args.pilot_review)}
    overrides_by_url = {row["source_url"]: row for row in load_csv(args.overrides)}

    output_rows: list[dict[str, str]] = []
    for record in records:
        url = record["source_url"]
        title = record["title_tr"]
        suggestion, suggestion_reason = suggest_status(title)
        pilot = pilot_by_url.get(url, {})
        override = overrides_by_url.get(url, {})

        output_rows.append(
            {
                "candidate_id": "PUB-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12],
                "index_file": record["index_file"],
                "rg_date": record["rg_date"],
                "rg_issue": record["rg_issue"],
                "channel_guess": record["channel_guess"],
                "title_tr": title,
                "matched_keywords": record["matched_keywords"],
                "source_url": url,
                "local_file": record["local_file"],
                "extraction_status": (
                    "manual_visual_review" if override else record["extraction_status"]
                ),
                "text_length": str(record["text_length"]),
                "auto_suggestion": suggestion,
                "suggested_type": suggest_type(title),
                "is_framework": "true" if "çerçeve" in title.casefold() else "false",
                "manual_date_signed": override.get("date_signed", ""),
                "manual_date_approved": override.get("date_approved", ""),
                "manual_law_no": override.get("law_no", ""),
                "review_status": pilot.get("status", "needs_review"),
                "agreement_id": pilot.get("agreement_id", ""),
                "review_reason": pilot.get("review_reason", suggestion_reason),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} review rows to {args.output}")
    for field in ("review_status", "auto_suggestion", "suggested_type", "extraction_status"):
        counts: dict[str, int] = {}
        for row in output_rows:
            value = row[field] or "blank"
            counts[value] = counts.get(value, 0) + 1
        print(f"{field}: {counts}")


if __name__ == "__main__":
    main()
