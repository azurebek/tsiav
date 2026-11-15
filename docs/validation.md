# Validation

## 2017 pilot

- Population: 22 included agreement records.
- Sample: 4 records (18.2%), selected with Python `random.Random(2017)`.
- Checked fields: partner, official Turkish title, type, signature date, approval
  date, law/decision number, Resmî Gazete date and issue, and source URL.
- Sample IDs: `TR-NER-2013-01`, `TR-CIV-2015-01`, `TR-GMB-2014-01`,
  `TR-MLI-2010-01`.
- Method: compared HTML law text and/or the rendered first and signature pages of
  the official Resmî Gazete PDF against the final CSV.
- Result: 0 field transcription/link errors in 4 sampled records (observed record
  error rate 0%).

Niger and Cote d'Ivoire were also checked against the coding rule: both have
`type = training` because training is the main substantive content, and
`is_framework = true` because their titles contain `çerçeve`.

## Full-corpus field audit

- Population: 111 core records outside the 22-record 2017 pilot.
- Frozen sample: 30 records (27.0%).
- Selection: deterministic SHA-256 ordering stratified to cover every approval
  year present in the non-pilot population, every `type`, every publication
  channel, both instrument levels, and both framework-flag values; remaining
  positions were filled by the same hash order.
- Checked fields: partner, official Turkish title, type, framework flag,
  signature date, approval date, law/decision number, Resmî Gazete date and
  issue, and official source URL.
- Evidence: official Resmî Gazete HTML text, OCR of official PDF first pages, or
  a separately documented official source for the Ethiopia split record.
- Result before correction: 27 records passed; 3 title defects were found.
- Corrections: the US demonstration-project No. 5 title, the Turkish `Gambiya`
  spelling, and the full Oman extension instrument title. No sampled date,
  document-number, issue, or source-link error was found.
- Result after correction: 30/30 sampled records pass with no unresolved audit
  item. Row-level evidence metadata is in `data/audit/field_audit_v1.csv`.

## Late-year coverage check

- The tracked index-coverage manifest records complete calendar-year caches for
  2010–2025 and coverage through the fixed 2026-11-13 snapshot for 2026.
- For 2025, 384 ordinary and supplementary index files produced 25 high-recall
  candidates. All 25 were resolved as domestic/administrative measures or
  deployment mandates; none was a bilateral defence-cooperation publication.
- The 2023, 2024, and 2026 candidate-to-inclusion funnel is shown explicitly in
  `VALIDATION_REPORT.md`; low final counts are therefore visible and testable
  rather than silently treated as a substantive trend.

## Known field limitation

`date_in_force` is not systematically extracted in v1.0.x and is blank in all
133 core rows. The column is retained only as a forward-compatible schema
placeholder and must not be interpreted substantively.
