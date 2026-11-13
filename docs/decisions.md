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
