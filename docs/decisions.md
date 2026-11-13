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
  memorandum. Full-run labels remain provisional until deduplication and quality
  review are complete.
