#!/usr/bin/env python3
"""Extract high-recall defence agreement candidates from cached indexes."""

from __future__ import annotations

import argparse
import csv
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


KEYWORDS = [
    "Askerî",
    "Askeri",
    "Savunma",
    "Savunma Sanayii",
    "Savunma Sanayi",
    "Askerî Eğitim",
    "Askeri Eğitim",
    "Askerî Mali",
    "Askeri Mali",
    "Askerî Çerçeve",
    "Askeri Çerçeve",
    "Eğitim, Teknik ve Bilimsel İşbirliği",
    "Eğitim, Teknik ve Bilimsel İş Birliği",
    "Silahlı Kuvvetler",
    "Harp",
    "Lojistik",
]


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current_href is not None:
            text = " ".join("".join(self.current_text).split())
            self.anchors.append((self.current_href, html.unescape(text)))
            self.current_href = None
            self.current_text = []


def decode_page(payload: bytes) -> str:
    return payload.decode("windows-1254", errors="replace")


def issue_number(page_text: str, filename: str) -> str:
    plain = re.sub(r"<[^>]+>", " ", page_text)
    plain = " ".join(html.unescape(plain).split())
    match = re.search(r"(?:Tarihli ve|tarihli ve)\s+(\d+)\s+Sayılı", plain)
    if not match:
        match = re.search(r"(?:Tarihli ve|tarihli ve)\s+(\d+)", plain)
    if not match:
        return ""
    extra_match = re.search(r"M(\d+)\.htm$", filename, re.IGNORECASE)
    if not extra_match:
        return match.group(1)
    extra_number = int(extra_match.group(1))
    label = "mukerrer" if extra_number == 1 else f"{extra_number}. mukerrer"
    return f"{match.group(1)} ({label})"


def channel_for(title: str) -> str:
    folded = title.casefold()
    if "uygun bulunduğuna dair kanun" in folded:
        return "law"
    if (
        "hakkında karar" in folded
        or "onaylanması hakkında karar" in folded
        or "yürürlüğe girmesi hakkında karar" in folded
        or re.match(r"^\d{4}/\d+", title)
    ):
        return "decision"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw/index"))
    parser.add_argument("--output", type=Path, default=Path("data/interim/candidates.csv"))
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2017)
    args = parser.parse_args()

    if args.start_year > args.end_year:
        parser.error("--start-year must be less than or equal to --end-year")

    rows: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    index_files = []
    for path in sorted(args.input.glob("*.htm")):
        match = re.fullmatch(r"(?P<day>\d{8})(?:M\d+)?\.htm", path.name, re.IGNORECASE)
        if not match:
            continue
        year = int(match.group("day")[:4])
        if args.start_year <= year <= args.end_year:
            index_files.append(path)

    for position, path in enumerate(index_files, start=1):
        page_text = decode_page(path.read_bytes())
        parser_ = AnchorParser()
        parser_.feed(page_text)
        day_key = path.name[:8]
        year = int(day_key[:4])
        base_url = (
            f"https://www.resmigazete.gov.tr/eskiler/{year}/{day_key[4:6]}/{path.name}"
        )
        document_pattern = re.compile(
            rf"^{day_key}(?:M\d+)?-\d+\.(?:htm|pdf)$",
            re.IGNORECASE,
        )

        for href, title in parser_.anchors:
            href_name = href.rsplit("/", 1)[-1]
            if not document_pattern.match(href_name):
                continue
            matched = [keyword for keyword in KEYWORDS if keyword.casefold() in title.casefold()]
            if not matched:
                continue
            source_url = urljoin(base_url, href)
            if source_url in seen_urls:
                continue
            seen_urls.add(source_url)
            rows.append(
                {
                    "index_file": path.name,
                    "rg_date": f"{day_key[:4]}-{day_key[4:6]}-{day_key[6:8]}",
                    "rg_issue": issue_number(page_text, path.name),
                    "channel_guess": channel_for(title),
                    "title_tr": title,
                    "matched_keywords": "; ".join(matched),
                    "source_url": source_url,
                }
            )

        if position % 500 == 0:
            print(
                f"Scanned {position}/{len(index_files)} indexes; "
                f"candidates={len(rows)}",
                flush=True,
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index_file",
        "rg_date",
        "rg_issue",
        "channel_guess",
        "title_tr",
        "matched_keywords",
        "source_url",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Wrote {len(rows)} candidates from {len(index_files)} indexes "
        f"({args.start_year}-{args.end_year}) to {args.output}"
    )


if __name__ == "__main__":
    main()
