#!/usr/bin/env python3
"""Create readable text copies and a JSON manifest for candidate documents."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"style", "script"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"style", "script"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def html_to_text(payload: bytes) -> str:
    source = payload.decode("windows-1254", errors="replace")
    parser = TextParser()
    parser.feed(source)
    text = html.unescape(" ".join(parser.parts))
    return re.sub(r"\s+", " ", text).strip()


def pdf_to_text(path: Path) -> str:
    """Extract searchable text from an official PDF."""
    reader = PdfReader(path)
    text = " ".join(page.extract_text() or "" for page in reader.pages)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=Path("data/interim/candidates.csv"))
    parser.add_argument("--docs", type=Path, default=Path("data/raw/docs"))
    parser.add_argument("--output", type=Path, default=Path("data/interim/extracted_docs.json"))
    args = parser.parse_args()

    with args.candidates.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    records = []
    for row in rows:
        filename = Path(urlparse(row["source_url"]).path).name
        source = args.docs / filename
        text = pdf_to_text(source) if source.suffix.lower() == ".pdf" else html_to_text(source.read_bytes())
        records.append({**row, "local_file": str(source), "text": text})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} extracted documents to {args.output}")


if __name__ == "__main__":
    main()
