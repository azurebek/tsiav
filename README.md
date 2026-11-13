# TSİAV 2017 pilot

This folder contains a reproducible pilot pipeline for bilateral defence
cooperation agreements published in the Resmî Gazete during 2017.

## Run

Use Python 3.11 or newer. Install the one PDF dependency first:

```powershell
python -m pip install -r requirements.txt
python scripts/01_download_index.py --year 2017 --delay 2.3
python scripts/02_filter.py
python scripts/03_fetch_docs.py --delay 2.3
python scripts/04_extract.py
python scripts/05_build_pilot.py
```

The download scripts cache every saved file and never re-download an existing
path. Raw files under `data/raw/` must not be edited manually.

## Outputs

- `data/interim/candidates.csv`: high-recall keyword matches.
- `data/interim/review.csv`: every candidate with inclusion status and reason.
- `data/interim/extracted_docs.json`: readable text for review.
- `data/final/tsiav_pilot_2017.csv`: one row per deduplicated agreement.

When a law and decision refer to the same agreement, the final CSV stores both
Resmî Gazete dates, issues, and URLs in law-then-decision order, separated by
semicolons.

## Full index download

The range runner downloads 2010 through the supplied cutoff date. It is safe to
restart because existing raw index files are skipped:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_full_download.ps1 `
  -StartYear 2010 -EndYear 2026 -Through 2026-10-27 -Delay 2.3
```

`type` records the agreement's main substantive content. `is_framework` separately
records whether the official Turkish title contains `çerçeve`, so a training
agreement can also be a framework agreement without forcing a single-category
tradeoff.
