#!/usr/bin/env python3
"""Download and cache daily Resmi Gazete index pages for one year."""

from __future__ import annotations

import argparse
import re
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://www.resmigazete.gov.tr/eskiler"
USER_AGENT = (
    "TSIAV academic dataset pilot/0.1 "
    "(ORCID 0009-0003-7141-0891)"
)


def date_range(year: int, through: date | None = None):
    current = date(year, 1, 1)
    stop = date(year + 1, 1, 1)
    if through is not None:
        stop = min(stop, through + timedelta(days=1))
    while current < stop:
        yield current
        current += timedelta(days=1)


def fetch(url: str, destination: Path, delay: float, last_request: list[float]) -> bool:
    """Fetch one URL with retries, respecting the delay between requests."""
    if destination.exists():
        return True

    elapsed = time.monotonic() - last_request[0]
    if elapsed < delay:
        time.sleep(delay - elapsed)

    for attempt in range(1, 4):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            last_request[0] = time.monotonic()
            with urlopen(request, timeout=45) as response:
                payload = response.read()
            destination.write_bytes(payload)
            return True
        except HTTPError as exc:
            if exc.code == 404:
                print(f"404 {url}", flush=True)
                return False
            error = exc
        except (URLError, TimeoutError, OSError) as exc:
            error = exc

        if attempt < 3:
            wait = delay * (2**attempt)
            print(f"Retry {attempt}/2 after {wait:.1f}s: {url} ({error})", flush=True)
            time.sleep(wait)

    raise RuntimeError(f"Repeated download failure: {url} ({error})")


def extra_issue_names(payload: bytes, day_key: str) -> list[str]:
    """Return linked extra issue index filenames such as 20171231M1.htm."""
    text = payload.decode("windows-1254", errors="replace")
    pattern = rf"{day_key}M\d+\.htm"
    return sorted(set(re.findall(pattern, text, flags=re.IGNORECASE)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2017)
    parser.add_argument(
        "--through",
        type=date.fromisoformat,
        help="Last publication date to request, in YYYY-MM-DD format.",
    )
    parser.add_argument("--delay", type=float, default=2.3)
    parser.add_argument("--output", type=Path, default=Path("data/raw/index"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    last_request = [0.0]
    downloaded = 0
    cached = 0
    extras = 0

    for position, day in enumerate(date_range(args.year, args.through), start=1):
        day_key = day.strftime("%Y%m%d")
        month = day.strftime("%m")
        filename = f"{day_key}.htm"
        destination = args.output / filename
        already_cached = destination.exists()
        url = f"{BASE_URL}/{args.year}/{month}/{filename}"

        if fetch(url, destination, args.delay, last_request):
            cached += int(already_cached)
            downloaded += int(not already_cached)
            for extra_name in extra_issue_names(destination.read_bytes(), day_key):
                extra_destination = args.output / extra_name
                extra_cached = extra_destination.exists()
                extra_url = f"{BASE_URL}/{args.year}/{month}/{extra_name}"
                if fetch(extra_url, extra_destination, args.delay, last_request):
                    cached += int(extra_cached)
                    downloaded += int(not extra_cached)
                    extras += 1

        if position % 25 == 0:
            print(
                f"Progress {position}: downloaded={downloaded}, cached={cached}, "
                f"linked_extras={extras}",
                flush=True,
            )

    print(
        f"Done: downloaded={downloaded}, cached={cached}, linked_extras={extras}",
        flush=True,
    )


if __name__ == "__main__":
    main()
