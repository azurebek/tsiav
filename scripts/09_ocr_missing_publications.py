#!/usr/bin/env python3
"""OCR page one of scanned PDFs whose signed date was not parsed."""

from __future__ import annotations

import argparse
import csv
import platform
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fields",
        type=Path,
        default=Path("data/interim/publication_fields.csv"),
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/interim/review_full.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/ocr_publication_text.csv"),
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=Path("tmp/ocr_publications"),
    )
    parser.add_argument("--dpi", type=int, default=170)
    parser.add_argument(
        "--ocr-engine",
        choices=("auto", "windows", "tesseract"),
        default="auto",
    )
    args = parser.parse_args()

    with args.fields.open(encoding="utf-8-sig", newline="") as handle:
        field_rows = list(csv.DictReader(handle))
    with args.review.open(encoding="utf-8-sig", newline="") as handle:
        review_rows = list(csv.DictReader(handle))
    review_by_url = {row["source_url"]: row for row in review_rows}

    targets = [
        row
        for row in field_rows
        if not row["date_signed"]
        and review_by_url.get(row["source_url"], {}).get("local_file", "").casefold().endswith(".pdf")
    ]
    existing: dict[str, dict[str, str]] = {}
    if args.output.exists():
        with args.output.open(encoding="utf-8-sig", newline="") as handle:
            existing = {row["source_url"]: row for row in csv.DictReader(handle)}

    pending = [
        row
        for row in targets
        if existing.get(row["source_url"], {}).get("ocr_status") != "ok"
    ]
    engine = args.ocr_engine
    if engine == "auto":
        if platform.system() == "Windows" and shutil.which("powershell.exe"):
            engine = "windows"
        elif shutil.which("tesseract"):
            engine = "tesseract"
        elif pending:
            raise SystemExit(
                "OCR is required but no engine is available. On Windows use the "
                "built-in Windows OCR path; on Linux/macOS install Tesseract with "
                "Turkish and English language data."
            )
    if pending and engine == "windows" and not shutil.which("powershell.exe"):
        raise SystemExit("--ocr-engine windows requires powershell.exe")
    if pending and engine == "tesseract" and not shutil.which("tesseract"):
        raise SystemExit("--ocr-engine tesseract requires the tesseract executable")

    args.temp_dir.mkdir(parents=True, exist_ok=True)
    ocr_script = Path(__file__).with_name("windows_ocr_image.ps1").resolve()
    output_rows = list(existing.values())
    output_by_url = dict(existing)

    for number, row in enumerate(targets, 1):
        url = row["source_url"]
        if output_by_url.get(url, {}).get("ocr_status") == "ok":
            continue

        source = Path(review_by_url[url]["local_file"])
        stem = row["candidate_id"]
        prefix = args.temp_dir / stem
        render = subprocess.run(
            [
                "pdftoppm",
                "-f",
                "1",
                "-l",
                "1",
                "-png",
                "-r",
                str(args.dpi),
                str(source),
                str(prefix),
            ],
            capture_output=True,
            text=True,
        )
        if render.returncode:
            item = {
                "candidate_id": row["candidate_id"],
                "source_url": url,
                "ocr_status": "render_error",
                "ocr_text": "",
                "ocr_error": render.stderr.strip(),
            }
        else:
            rendered_images = sorted(args.temp_dir.glob(f"{stem}-*.png"))
            if not rendered_images:
                item = {
                    "candidate_id": row["candidate_id"],
                    "source_url": url,
                    "ocr_status": "render_error",
                    "ocr_text": "",
                    "ocr_error": "pdftoppm reported success but produced no PNG.",
                }
                if url in output_by_url:
                    output_rows[output_rows.index(output_by_url[url])] = item
                else:
                    output_rows.append(item)
                output_by_url[url] = item
                continue
            image = rendered_images[0]
            if engine == "windows":
                command = [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ocr_script),
                    "-ImagePath",
                    str(image.resolve()),
                ]
                encoding = "utf-8-sig"
            else:
                command = [
                    "tesseract",
                    str(image.resolve()),
                    "stdout",
                    "-l",
                    "tur+eng",
                    "--psm",
                    "6",
                ]
                encoding = "utf-8"
            recognize = subprocess.run(
                command,
                capture_output=True,
                encoding=encoding,
                errors="replace",
            )
            item = {
                "candidate_id": row["candidate_id"],
                "source_url": url,
                "ocr_status": "ok" if recognize.returncode == 0 else "ocr_error",
                "ocr_text": recognize.stdout.strip() if recognize.returncode == 0 else "",
                "ocr_error": recognize.stderr.strip() if recognize.returncode else "",
            }

        if url in output_by_url:
            output_rows[output_rows.index(output_by_url[url])] = item
        else:
            output_rows.append(item)
        output_by_url[url] = item

        if number % 10 == 0 or number == len(targets):
            print(f"OCR progress: {number}/{len(targets)}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["candidate_id", "source_url", "ocr_status", "ocr_text", "ocr_error"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    ok_count = sum(row["ocr_status"] == "ok" for row in output_rows)
    print(
        f"Wrote {len(output_rows)} OCR rows to {args.output}; "
        f"ok={ok_count}; engine={engine}"
    )


if __name__ == "__main__":
    main()
