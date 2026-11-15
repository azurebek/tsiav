# TSİAV dataset pipeline

This repository contains a reproducible pipeline for bilateral defence
cooperation agreements published in the Resmî Gazete from 2010 through the
2026-11-13 snapshot. The manually reviewed 2017 dataset remains the regression
fixture for the full run.

Column definitions and coding rules are documented in `CODEBOOK.md`. Release
counts, coverage, distributions, and automated integrity checks are recorded in
`VALIDATION_REPORT.md`.

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
- `data/final/tsiav_2010_2026.csv`: confirmed 2010–2026 core sample.
- `data/final/tsiav_2010_2026_extended.csv`: core sample plus coded
  non-military security-force instruments for robustness checks.

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
- `data/interim/manual_group_overrides.csv`: title and primary-content corrections
  made during agreement-level review.
- `data/interim/manual_group_review_batches.csv`: frozen count and SHA-256 digest
  for the manually reviewed agreement batch.
- `data/interim/manual_group_splits.csv`: explicit rows for publications that
  approve more than one legal instrument.
- `data/interim/manual_scope_overrides.csv`: documented core/extended boundary
  decisions and actor-level metadata.
- `data/interim/provisional_agreement_groups.csv`: law and decision publications
  grouped into provisional agreement records.
- `data/interim/publication_fields.csv`: publication-level document numbers,
  signed dates, and approval dates with their extraction source.
- `data/interim/provisional_dataset.csv`: one row per deduplicated agreement group,
  including scope status and reason.
- `data/interim/dataset_draft.csv`: confirmed rows used to materialize the core
  dataset.
- `data/interim/scope_exceptions.csv`: clear exclusions and coded extended-only
  instruments kept outside the core draft.
- `data/interim/exclusion_log.csv`: publication-level exclusions and reasons.

After the cached collection exists, rebuild every review artifact with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_full_processing.ps1
```

The equivalent cross-platform runners are:

```bash
python scripts/run_full_collection.py --start-year 2010 --end-year 2026 --through 2026-11-13
python scripts/run_full_processing.py
python scripts/run_validation.py
```

Fresh OCR uses Windows OCR when available and otherwise falls back to Tesseract
with Turkish and English language data. Poppler's `pdftoppm` is required for
rendering scanned PDF pages. GitHub Actions runs the unit tests and validates the
committed release artifacts on every push and pull request; it does not repeat
the multi-hour network collection job.

The processing runner uses Windows OCR for scanned first pages and then reruns
field extraction. Visually verified OCR exceptions are stored explicitly in
`manual_extraction_overrides.csv`.

One failed document does not stop the whole download batch. Re-running the same
command retries only missing documents.

`type` records the agreement's main substantive content. `is_framework` separately
records whether the official Turkish title contains `çerçeve`, so a training
agreement can also be a framework agreement without forcing a single-category
tradeoff.

Non-military security forces (`coast_guard`, `gendarmerie`, and `police`) are
coded in the extended layer but excluded from the core sample. The
`partner_recognition` field is descriptive: `limited` does not by itself remove
an otherwise in-scope military agreement from the core sample.

The full-corpus field audit and index-coverage evidence are stored under
`data/audit/`. `date_in_force` is reserved but not systematically extracted in
the v1.0.x releases and is blank in every row; see the codebook and validation
report before using that column.
