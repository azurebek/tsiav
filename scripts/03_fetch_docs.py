#!/usr/bin/env python3
"""Download and cache full text HTML for candidate records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "TSIAV academic dataset pilot/0.1 "
    "(ORCID 0009-0003-7141-0891)"
)


def local_name(url: str) -> str:
    name = Path(urlparse(url).path).name
    if name:
        return name
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + ".htm"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/interim/candidates.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/docs"))
    parser.add_argument("--delay", type=float, default=2.3)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    last_request = 0.0
    downloaded = 0
    cached = 0
    for position, row in enumerate(rows, start=1):
        url = row["source_url"]
        destination = args.output / local_name(url)
        if destination.exists():
            cached += 1
            continue

        elapsed = time.monotonic() - last_request
        if elapsed < args.delay:
            time.sleep(args.delay - elapsed)

        error: Exception | None = None
        for attempt in range(1, 4):
            try:
                request = Request(url, headers={"User-Agent": USER_AGENT})
                last_request = time.monotonic()
                with urlopen(request, timeout=45) as response:
                    destination.write_bytes(response.read())
                downloaded += 1
                error = None
                break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                error = exc
                if attempt < 3:
                    time.sleep(args.delay * (2**attempt))
        if error is not None:
            raise RuntimeError(f"Repeated download failure: {url} ({error})")
        if position % 20 == 0:
            print(f"Progress {position}/{len(rows)}", flush=True)

    print(f"Done: downloaded={downloaded}, cached={cached}")


if __name__ == "__main__":
    main()
