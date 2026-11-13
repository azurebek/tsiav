# TSİAV dataset pipeline

This repository contains a reproducible pipeline for bilateral defence
cooperation agreements published in the Resmî Gazete from 2010 through the
2026-11-13 snapshot. The manually reviewed 2017 dataset remains the regression
fixture for the full run.

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

## Full collection run

The collection runner updates cached indexes through a fixed snapshot date,
filters all requested years, downloads candidate documents, and extracts their
text. It is safe to restart because existing raw files are skipped:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_full_collection.ps1 `
  -StartYear 2010 -EndYear 2026 -Through 2026-11-13 -Delay 2.3
```

The full-run intermediate outputs are:

- `data/interim/candidates_full.csv`: high-recall matches across 2010–2026.
- `data/interim/download_failures.csv`: URLs that still failed after retries.
- `data/interim/extracted_docs_full.json`: extracted text plus a per-document
  extraction status. Full extracted text is generated locally and is not tracked
  in Git.
- `data/interim/review_full.csv`: conservative review queue. Automated labels are
  suggestions only; only the previously validated 2017 pilot rows start with a
  final review status.
- `data/interim/manual_extraction_overrides.csv`: fields recovered by visual PDF
  review when automated text extraction was inadequate.
- `data/interim/manual_review_overrides.csv`: documented manual resolutions for
  records whose index titles are truncated or otherwise not classifiable by rule.
- `data/interim/provisional_agreement_groups.csv`: law and decision publications
  grouped into provisional agreement records.
- `data/interim/publication_fields.csv`: publication-level document numbers,
  signed dates, and approval dates with their extraction source.
- `data/interim/provisional_dataset.csv`: one row per deduplicated agreement group,
  including scope status and reason.
- `data/interim/dataset_draft.csv`: current in-scope draft. It is not a final
  release while rows remain provisional.
- `data/interim/scope_exceptions.csv`: out-of-scope, split-required, and
  user-decision items kept outside the draft.
- `data/interim/exclusion_log.csv`: publication-level exclusions and reasons.

After the cached collection exists, rebuild every review artifact with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_full_processing.ps1
```

The processing runner uses Windows OCR for scanned first pages and then reruns
field extraction. Visually verified OCR exceptions are stored explicitly in
`manual_extraction_overrides.csv`.

One failed document does not stop the whole download batch. Re-running the same
command retries only missing documents.

`type` records the agreement's main substantive content. `is_framework` separately
records whether the official Turkish title contains `çerçeve`, so a training
agreement can also be a framework agreement without forcing a single-category
tradeoff.
