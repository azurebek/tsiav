#!/usr/bin/env python3
"""Build one provisional dataset row per deduplicated agreement group."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def split_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def clean_title(title: str) -> str:
    value = re.sub(r"^[–—\-\s]+", "", title).strip()
    value = re.sub(r"^(?:\d{4}/\d+|\d{3,5})\s+", "", value).strip()
    value = re.sub(r"\s*\(Karar\s+Sayısı:.*\)\s*$", "", value, flags=re.IGNORECASE)
    marker = re.search(
        r"\s+(?:Onaylanmas[ıi]\w*|Yürürlüğe\s+Girmesi)\b",
        value,
        re.IGNORECASE,
    )
    if marker:
        value = value[: marker.start()]
    value = re.sub(
        r"\s+Arasında\s+İmzalanan\s+[“\"]",
        " Arasında ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\s+(?:İlişik\s+)?Notalarla\s+Birlikte$", "", value, flags=re.IGNORECASE)
    terminal_forms = (
        (r"Anlaşmas[ıi](?:['’”\"]?n[ıi]n)$", "Anlaşması"),
        (r"Anlaşma[’'”\"]?n[ıi]n$", "Anlaşma"),
        (r"Muht[ıi]ras[ıi](?:['’”\"]?n[ıi]n)$", "Muhtırası"),
        (r"Muht[ıi]ra[’'”\"]?n[ıi]n$", "Muhtıra"),
        (r"Protokolü[’'”\"]?nün$", "Protokolü"),
        (r"Protokolünün$", "Protokolü"),
        (r"Protokol[’'”\"]?ün$", "Protokol"),
        (r"Düzenleme[’']?nin$", "Düzenleme"),
        (r"Değişiklik[’'”\"]?in$", "Değişiklik"),
    )
    for pattern, replacement in terminal_forms:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    value = value.strip(" ;,\"“”")
    return value


def fold_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks.replace("ı", "i")


def infer_actor_type(title: str) -> str:
    folded = fold_for_match(title)
    if "sahil guvenlik" in folded:
        return "coast_guard"
    if "jandarma" in folded:
        return "gendarmerie"
    if "polis" in folded or "emniyet" in folded:
        return "police"
    return "military"


def infer_partner_recognition(partner: str) -> str:
    if not partner:
        return ""
    if partner.endswith("(XKX)") or partner.endswith("(XNC)"):
        return "limited"
    return "un_member"


def infer_instrument_level(title: str) -> str:
    folded = fold_for_match(title)
    if (
        "hukumeti" in folded
        or "bakanlar kurulu" in folded
        or folded.startswith("turkiye cumhuriyeti ile ")
    ):
        return "intergovernmental"
    return "inter-agency"


def scope_suggestion(title: str, confirmed: bool) -> tuple[str, str]:
    if confirmed:
        return "confirmed_in", "Included by the manually reviewed 2017 pilot."

    folded = fold_for_match(title)
    if "nato bakim ve ikmal ajansi" in folded or "nato danisma, komuta ve kontrol ajansi" in folded:
        return "auto_exclude", "Counterparty is a NATO agency rather than a bilateral country partner."
    if "ukrayna savunma bakanligi ve avrupa muttefik kuvvetleri" in folded:
        return "auto_exclude", "Three-party instrument; outside the bilateral scope."
    if "macaristan savunma bakanligi ve polonya" in folded:
        return "auto_exclude", "Three-party instrument; outside the bilateral scope."
    if "azerbaycan cumhuriyeti hukumeti, gurcistan hukumeti ve turkiye" in folded:
        return "auto_exclude", "Three-country instrument; outside the bilateral scope."
    if folded.count("turkiye cumhuriyeti hukumeti ile") >= 2 and "1 numarali degisiklik" in folded:
        return "split_required", "One decision approves both a framework agreement and its first amendment."
    if folded.count("teknik duzenleme") >= 2:
        return "split_required", "One publication contains two separate bilateral technical arrangements."
    if "sahil guvenlik komutanligi" in folded:
        return "needs_user_review", "Coast Guard-only instrument; scope treatment needs a substantive decision."
    return "provisional_in", "Bilateral military or defence cooperation title."


def main() -> None:
    parser = argparse.ArgumentParser()
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
    parser.add_argument(
        "--fields",
        type=Path,
        default=Path("data/interim/publication_fields.csv"),
    )
    parser.add_argument("--pilot", type=Path, default=Path("data/final/tsiav_pilot_2017.csv"))
    parser.add_argument(
        "--partner-aliases",
        type=Path,
        default=Path("data/reference/partner_aliases.csv"),
    )
    parser.add_argument(
        "--group-overrides",
        type=Path,
        default=Path("data/interim/manual_group_overrides.csv"),
    )
    parser.add_argument(
        "--review-batches",
        type=Path,
        default=Path("data/interim/manual_group_review_batches.csv"),
    )
    parser.add_argument(
        "--group-splits",
        type=Path,
        default=Path("data/interim/manual_group_splits.csv"),
    )
    parser.add_argument(
        "--scope-overrides",
        type=Path,
        default=Path("data/interim/manual_scope_overrides.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/provisional_dataset.csv"),
    )
    args = parser.parse_args()

    with args.groups.open(encoding="utf-8-sig", newline="") as handle:
        groups = list(csv.DictReader(handle))
    with args.members.open(encoding="utf-8-sig", newline="") as handle:
        members = list(csv.DictReader(handle))
    with args.fields.open(encoding="utf-8-sig", newline="") as handle:
        fields = list(csv.DictReader(handle))
    with args.pilot.open(encoding="utf-8-sig", newline="") as handle:
        pilot = list(csv.DictReader(handle))
    with args.partner_aliases.open(encoding="utf-8-sig", newline="") as handle:
        partner_aliases = list(csv.DictReader(handle))
    with args.group_overrides.open(encoding="utf-8-sig", newline="") as handle:
        group_overrides = {
            row["group_id"]: row for row in csv.DictReader(handle)
        }
    with args.review_batches.open(encoding="utf-8-sig", newline="") as handle:
        review_batches = list(csv.DictReader(handle))
    with args.group_splits.open(encoding="utf-8-sig", newline="") as handle:
        group_splits: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in csv.DictReader(handle):
            group_splits[row["source_group_id"]].append(row)
    with args.scope_overrides.open(encoding="utf-8-sig", newline="") as handle:
        scope_overrides = {
            row["group_id"]: row for row in csv.DictReader(handle)
        }

    members_by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in members:
        members_by_group[item["group_id"]].append(item)
    fields_by_candidate = {item["candidate_id"]: item for item in fields}
    pilot_by_url: dict[str, dict[str, str]] = {}
    for item in pilot:
        for source_url in split_values(item["source_url"]):
            pilot_by_url[source_url] = item

    output_rows: list[dict[str, str]] = []
    for group in groups:
        group_members = members_by_group[group["group_id"]]
        publication_fields = [
            fields_by_candidate[item["candidate_id"]]
            for item in group_members
            if item["candidate_id"] in fields_by_candidate
        ]
        source_urls = unique([item["source_url"] for item in group_members])
        confirmed = next((pilot_by_url[url] for url in source_urls if url in pilot_by_url), None)

        raw_titles = split_values(group["titles"])
        title = confirmed["title_tr"] if confirmed else clean_title(raw_titles[0])
        group_override = group_overrides.get(group["group_id"], {})
        title = group_override.get("title_tr") or title
        scope_status, scope_reason = scope_suggestion(title, confirmed is not None)
        folded_title = fold_for_match(title)
        partner_matches = {
            (item["partner"], item["iso3"])
            for item in partner_aliases
            if re.search(rf"\b{re.escape(fold_for_match(item['alias_tr']))}\b", folded_title)
        }
        partner = (
            confirmed["partner"]
            if confirmed
            else f"{next(iter(partner_matches))[0]} ({next(iter(partner_matches))[1]})"
            if len(partner_matches) == 1
            else ""
        )

        signed_dates = unique([item["date_signed"] for item in publication_fields])
        decision_approvals = unique(
            [item["date_approved"] for item in publication_fields if item["decision_no"]]
        )
        law_approvals = unique(
            [item["date_approved"] for item in publication_fields if item["law_no"]]
        )
        law_numbers = unique([item["law_no"] for item in publication_fields])
        decision_numbers = unique([item["decision_no"] for item in publication_fields])

        date_signed = confirmed["date_signed"] if confirmed else (max(signed_dates) if signed_dates else "")
        date_approved = (
            confirmed["date_approved"]
            if confirmed
            else max(decision_approvals)
            if decision_approvals
            else max(law_approvals)
            if law_approvals
            else ""
        )
        channel = (
            confirmed["channel"]
            if confirmed
            else "both"
            if law_numbers and decision_numbers
            else "law"
            if law_numbers
            else "decision"
            if decision_numbers
            else group["channels"]
        )

        notes: list[str] = []
        if len(signed_dates) > 1 and not confirmed:
            notes.append("Multiple signed dates found; later date selected provisionally.")
        if not date_signed:
            notes.append("Signed date requires manual extraction or confirmation.")
        if not date_approved:
            notes.append("Approval date requires manual extraction or confirmation.")
        if not partner:
            notes.append("Partner requires manual confirmation.")
        if not confirmed:
            notes.append("Provisional row; title-level scope and parsed fields are not yet fully reviewed.")
        if group_override.get("notes"):
            notes.append(group_override["notes"])

        output_rows.append(
            {
                "id": confirmed["id"] if confirmed else group["group_id"],
                "partner": partner,
                "title_tr": title,
                "type": (
                    confirmed["type"]
                    if confirmed
                    else group_override.get("type")
                    if group_override.get("type")
                    else (split_values(group["suggested_types"]) or ["other_military"])[0]
                ),
                "is_framework": confirmed["is_framework"] if confirmed else group["is_framework"],
                "date_signed": date_signed,
                "date_approved": date_approved,
                "date_in_force": confirmed["date_in_force"] if confirmed else "",
                "channel": channel,
                "law_no": confirmed["law_no"] if confirmed else "; ".join(law_numbers),
                "decision_no": confirmed["decision_no"] if confirmed else "; ".join(decision_numbers),
                "rg_date": confirmed["rg_date"] if confirmed else group["rg_dates"],
                "rg_issue": confirmed["rg_issue"] if confirmed else group["rg_issues"],
                "source_url": confirmed["source_url"] if confirmed else "; ".join(source_urls),
                "notes": confirmed["notes"] if confirmed else " ".join(notes),
                "status": "included" if confirmed else "provisional",
                "scope_status": scope_status,
                "scope_reason": scope_reason,
                "actor_type": infer_actor_type(title),
                "partner_recognition": infer_partner_recognition(partner),
                "instrument_level": infer_instrument_level(title),
                "core_sample": "true" if scope_status in {"confirmed_in", "provisional_in"} else "false",
            }
        )

    for batch in review_batches:
        selected = [
            row for row in output_rows if row["scope_status"] == batch["selection"]
        ]
        selected_ids = sorted(row["id"] for row in selected)
        digest = hashlib.sha256("\n".join(selected_ids).encode("utf-8")).hexdigest()
        if len(selected) != int(batch["expected_count"]) or digest != batch["group_ids_sha256"]:
            raise ValueError(
                "Manual review batch does not match the generated group set: "
                f"snapshot={batch['snapshot']} count={len(selected)} sha256={digest}"
            )
        for row in selected:
            row["status"] = batch["review_status"]
            row["scope_status"] = "confirmed_in"
            row["scope_reason"] = batch["review_reason"]
            row["notes"] = row["notes"].replace(
                "Provisional row; title-level scope and parsed fields are not yet fully reviewed.",
                "",
            ).strip()
            row["notes"] = (
                row["notes"] + " " + f"Manual title review batch: {batch['snapshot']}."
            ).strip()

    expanded_rows: list[dict[str, str]] = []
    for row in output_rows:
        splits = group_splits.get(row["id"], [])
        if not splits:
            expanded_rows.append(row)
            continue
        for split in splits:
            split_row = dict(row)
            split_row.update(
                {
                    "id": split["split_id"],
                    "partner": split["partner"],
                    "title_tr": split["title_tr"],
                    "type": split["type"],
                    "is_framework": split["is_framework"],
                    "date_signed": split["date_signed"],
                    "notes": split["notes"],
                    "status": "included",
                    "scope_status": "confirmed_in",
                    "scope_reason": "Multi-instrument publication manually split into legal instruments.",
                }
            )
            expanded_rows.append(split_row)
    output_rows = expanded_rows

    for row in output_rows:
        row["actor_type"] = infer_actor_type(row["title_tr"])
        row["partner_recognition"] = infer_partner_recognition(row["partner"])
        row["instrument_level"] = infer_instrument_level(row["title_tr"])
        row["core_sample"] = (
            "true" if row["scope_status"] in {"confirmed_in", "provisional_in"} else "false"
        )
        override = scope_overrides.get(row["id"])
        if not override:
            continue
        row["scope_status"] = override["scope_status"]
        row["scope_reason"] = override["scope_reason"]
        row["actor_type"] = override["actor_type"]
        row["partner_recognition"] = override["partner_recognition"]
        row["instrument_level"] = override["instrument_level"]
        row["core_sample"] = override["core_sample"]
        row["status"] = "included"
        row["notes"] = row["notes"].replace(
            "Provisional row; title-level scope and parsed fields are not yet fully reviewed.",
            "",
        ).strip()
        row["notes"] = (row["notes"] + " " + override["notes"]).strip()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields_out = list(output_rows[0])
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields_out)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} agreement rows to {args.output}")
    for status in (
        "confirmed_in",
        "provisional_in",
        "extended_only",
        "needs_user_review",
        "split_required",
        "auto_exclude",
    ):
        print(f"{status}: {sum(row['scope_status'] == status for row in output_rows)}")
    print(f"Missing signed date: {sum(not row['date_signed'] for row in output_rows)}")
    print(f"Missing approval date: {sum(not row['date_approved'] for row in output_rows)}")
    print(f"Missing partner: {sum(not row['partner'] for row in output_rows)}")


if __name__ == "__main__":
    main()
