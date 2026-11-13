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
    status_counts: dict[str, int] = {}
    for position, row in enumerate(rows, start=1):
        filename = Path(urlparse(row["source_url"]).path).name
        source = args.docs / filename
        text = ""
        error = ""
        if not source.exists():
            status = "missing_file"
        else:
            try:
                text = (
                    pdf_to_text(source)
                    if source.suffix.lower() == ".pdf"
                    else html_to_text(source.read_bytes())
                )
                if not text:
                    status = "empty_text"
                elif len(text) < 100:
                    status = "short_text"
                else:
                    status = "ok"
            except Exception as exc:  # Preserve the batch and log the document-level error.
                status = "extraction_error"
                error = repr(exc)

        status_counts[status] = status_counts.get(status, 0) + 1
        records.append(
            {
                **row,
                "local_file": str(source),
                "extraction_status": status,
                "text_length": len(text),
                "extraction_error": error,
                "text": text,
            }
        )
        if position % 50 == 0:
            print(f"Progress {position}/{len(rows)}: {status_counts}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(records)} extracted documents to {args.output}; "
        f"statuses={status_counts}"
    )


if __name__ == "__main__":
    main()
