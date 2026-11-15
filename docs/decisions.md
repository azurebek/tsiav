# Decisions log

## 2017 pilot

- Scope follows publication in the Resmî Gazete, not all agreements signed by Türkiye.
- Both approval laws and approval decisions are searched.
- Candidate filtering favours recall. False positives remain visible in `review.csv`
  with an exclusion reason.
- Unknown fields are left blank in CSV and explained in `notes`.
- The high-recall filter returned 113 candidate publications. Manual title and
  full-text review retained 37 publication records belonging to 22 unique bilateral
  defence documents and excluded 76 domestic or otherwise out-of-scope publications.
  Law and decision publications were merged.
- Military logistics support/grants and exercise host-nation support are coded
  `other_military`; defence-project and defence-classified-information instruments
  are coded `defence_industry`.
- `type` records the agreement's main substantive content. `is_framework` is a
  separate boolean flag and is `true` whenever the official Turkish title contains
  `çerçeve`. Thus titles such as `Askerî Eğitim, Teknik ve Bilimsel İş Birliği
  Çerçeve Anlaşması` are coded `type = training` and `is_framework = true`.
- For agreements signed by the parties on different dates, `date_signed` records
  the later date and `notes` preserves both dates. This applies to Niger.
- `date_approved` uses the Council of Ministers decision date when a decision is
  available; for law-only records it uses the law's acceptance date.
- When both channels exist, `rg_date`, `rg_issue`, and `source_url` store the law
  reference first and the decision reference second, separated by semicolons.

## 2010–2026 full run

- The first full-run snapshot is frozen at 2026-11-13. Later updates must use a
  new documented snapshot date rather than silently changing the coverage.
- The 2017 pilot outputs remain unchanged and serve as regression fixtures while
  the full-run pipeline is developed.
- Full-run collection is resumable. A document-level network or extraction error
  is logged and does not discard successful work from the rest of the batch.
- The high-recall filter found 1,165 unique candidate publication URLs across
  7,061 cached index pages. Substantive inclusion and deduplication are still
  pending; this count is not an agreement count.
- Automated PDF text extraction returned 1,105 normal texts, 51 short texts, and
  9 empty texts. Title review showed that 58 of the 60 low-text PDFs are clear
  out-of-scope domestic or deployment records. The two potentially in-scope law
  pages (Gabon Law 6657 and Somalia Law 6670) were rendered and visually reviewed;
  their dates and law numbers are recorded in `manual_extraction_overrides.csv`.
- Automated review rules are conservative suggestions, not silent final coding.
  Against the completed 2017 pilot they suggested 35 inclusions and 69 exclusions,
  all correctly, while leaving 9 records for review. No confirmed 2017 inclusion
  was automatically excluded.
- After normalizing historical spelling and diacritics and adding explicit
  out-of-scope rules, the review classifier reproduced all 113 pilot judgments:
  all 37 included publications were suggested for inclusion and all 76 excluded
  publications were suggested for exclusion, with no pilot misclassification.
- Across the full corpus the calibrated rules suggest 193 inclusions and 971
  exclusions. The one remaining truncated title was resolved from its full saved
  text as the 2010 Türkiye-South Korea military student exchange and education
  memorandum. These suggestions were subsequently deduplicated and manually
  reviewed; they are not treated as final labels on their own.
- Title canonicalization and law/decision deduplication reduce 194 provisionally
  included publications (the 193 title suggestions plus the manual South Korea
  override) to 139 provisional agreement groups. The 2017 regression remains
  exactly 37 publications and 22 agreements.
- Scanned first pages are OCRed locally with the installed Turkish Windows OCR
  engine. OCR output is retained separately and never treated as a silent manual
  correction. Twelve publications with inadequate machine text were visually
  verified and recorded in `manual_extraction_overrides.csv`.
- Publication-level extraction recovers a document number for all 194
  provisionally included publications, a signed date for 185, and an approval
  date for 193. After agreement-level consolidation and documented manual source
  checks, approval date coverage is complete and only the Jordan S-70 training
  protocol still lacks a signed date.
- Scope review yields 133 core inclusions, 7 clear bilateral-scope exclusions,
  and 1 Coast Guard-only instrument retained in the extended layer. There are no
  unresolved scope decisions in this snapshot.
- The 107 title-level provisional inclusions were subsequently reviewed as a
  frozen batch. The batch records the expected row count and SHA-256 digest of the
  sorted group IDs so a future pipeline change cannot silently inherit the manual
  approval. Seven primary-content type corrections and one recovered full title
  are stored in `manual_group_overrides.csv`.
- Two multi-instrument publications are split explicitly in
  `manual_group_splits.csv`: decision 2011/2212 becomes separate Ethiopia
  framework-agreement and amendment rows, while decision 2018/12002 becomes
  separate Qatar and Saudi Arabia host-nation-support rows. Each split row keeps
  the shared official source. The Ethiopia amendment signing date (2008-05-16)
  is taken from the official TBMM bill and Foreign Affairs Committee report,
  because it is not exposed in the retrievable Resmî Gazete text.

## Core and extended samples

- Non-military security forces (coast guard, gendarmerie, and police) are coded
  but excluded from the core sample. They may be retained as `extended_only` for
  robustness checks. This is a general coding rule, not a one-off decision.
- Decision 2010/304 is retained only in the extended dataset. Its official title
  identifies the Turkish Coast Guard Command and the Northern Cyprus Security
  Forces Command as the parties, so it is coded `actor_type = coast_guard`,
  `instrument_level = inter-agency`, `partner_recognition = limited`, and
  `core_sample = false`. Council of Ministers approval is preserved in the
  existing `channel` and `decision_no` fields; it does not change the parties to
  the protocol.
- `partner_recognition` is descriptive rather than an automatic core filter.
  Northern Cyprus and Kosovo are coded `limited`; otherwise in-scope military
  agreements with Kosovo remain in the core sample. This keeps recognition and
  actor-type sensitivity tests analytically separable.
- `instrument_level` is coded from the official title: an instrument naming a
  government or the states themselves as parties is `intergovernmental`; an
  instrument naming ministries, general staffs, service commands, academies, or
  security-force commands without a government party is `inter-agency`.
- A 30-record stratified audit of the 111 non-pilot core rows found three title
  defects and no sampled date, number, issue, or link error. The corrected titles
  and row-level audit results are retained in explicit override/audit files.
- `date_in_force` was not systematically collected for v1.0.x. It remains a
  reserved all-blank column and is disclosed as such in the codebook and
  validation report.
