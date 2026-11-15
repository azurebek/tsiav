# TSİAV 2010–2026 validation report

Snapshot: `2026-11-13`

## Release summary

| Measure | Result |
| --- | --- |
| Core agreement rows | 133 |
| Extended agreement rows | 134 |
| Extended-only rows | 1 |
| Core partner entities | 62 |
| Candidate publication URLs reviewed | 1165 |
| Included publication records | 194 |
| Excluded publication records | 971 |
| Unresolved publication records | 0 |
| Core official-source references | 185 |
| Unique core official-source URLs | 183 |
| Core rows with signed date | 132 |
| Core rows with approval date | 133 |
| Core rows with date in force | 0 |
| Core framework-title rows | 19 |
| New-corpus field-audit sample | 30 |

## Automated checks

- PASS — Unique IDs in both release files
- PASS — Identical core and extended schemas
- PASS — Extended release equals core plus extended-only records
- PASS — All core rows are confirmed and marked `core_sample = true`
- PASS — Every released row has an official Resmî Gazete URL
- PASS — Source URL, issue, and publication-date list lengths align
- PASS — All approval dates are present and chronologically valid
- PASS — `is_framework` exactly matches `çerçeve` in the official title
- PASS — Non-military security-force records do not enter the core sample
- PASS — No unresolved split or user-review status remains
- PASS — No stale provisional note remains in either release
- PASS — All publication-level review rows have a final disposition
- PASS — The documented field-audit sample has no unresolved result

## Known data limitation

- `GRP-c7636962ffb6` (Jordan (JOR)): `date_signed` is blank; the official approval and publication fields are complete.
- `date_in_force` is not systematically extracted in this release and is blank in all 133 core rows. The reserved column must not be treated as evidence that an instrument never entered into force.

## New-corpus field audit

| Measure | Result |
| --- | --- |
| Non-pilot core population | 111 |
| Stratified sample checked | 30 |
| Passed without correction | 27 |
| Corrected during audit | 3 |
| Unresolved audit rows | 0 |

The frozen sample covers approval years, content types, publication channels, instrument levels, and both framework-flag values. Fields were compared with official Resmî Gazete HTML text, official-PDF OCR, or a separately documented official source. Three title defects were corrected; no sampled date, document-number, issue, or source-link error was found. Row-level results are stored in `data/audit/field_audit_v1.csv`.

## Publication funnel by Resmî Gazete year

| RG year | Index files | Candidates | Included publications | Excluded publications | Core source refs |
| --- | --- | --- | --- | --- | --- |
| 2010 | 403 | 98 | 12 | 86 | 7 |
| 2011 | 424 | 94 | 17 | 77 | 16 |
| 2012 | 406 | 91 | 9 | 82 | 9 |
| 2013 | 414 | 84 | 12 | 72 | 12 |
| 2014 | 439 | 92 | 6 | 86 | 6 |
| 2015 | 442 | 87 | 9 | 78 | 9 |
| 2016 | 447 | 130 | 20 | 110 | 20 |
| 2017 | 461 | 113 | 37 | 76 | 37 |
| 2018 | 473 | 90 | 25 | 65 | 24 |
| 2019 | 423 | 31 | 8 | 23 | 6 |
| 2020 | 405 | 52 | 7 | 45 | 7 |
| 2021 | 411 | 48 | 11 | 37 | 11 |
| 2022 | 398 | 53 | 12 | 41 | 12 |
| 2023 | 412 | 31 | 3 | 28 | 3 |
| 2024 | 395 | 26 | 4 | 22 | 4 |
| 2025 | 384 | 25 | 0 | 25 | 0 |
| 2026 | 324 | 20 | 2 | 18 | 2 |

The zero for 2025 is supported by a complete calendar-year index cache: 384 ordinary and supplementary index files produced 25 candidates, and all 25 were resolved as domestic/administrative measures or deployment mandates rather than bilateral defence-cooperation instruments. The low 2023–2024 and 2026 totals likewise follow the included-publication funnel; 2026 is covered only through the fixed 2026-11-13 snapshot.

## Core distribution by type

| Type | Rows |
| --- | --- |
| defence_industry | 34 |
| framework | 11 |
| other_military | 30 |
| protocol_amendment | 11 |
| training | 47 |

## Core distribution by approval year

| Approval year | Rows |
| --- | --- |
| 2010 | 5 |
| 2011 | 16 |
| 2012 | 7 |
| 2013 | 10 |
| 2014 | 5 |
| 2015 | 5 |
| 2016 | 17 |
| 2017 | 21 |
| 2018 | 19 |
| 2019 | 5 |
| 2020 | 4 |
| 2021 | 7 |
| 2022 | 7 |
| 2023 | 2 |
| 2024 | 2 |
| 2026 | 1 |

## Core distribution by publication channel

| Channel | Rows |
| --- | --- |
| both | 52 |
| decision | 73 |
| law | 8 |

## Core distribution by instrument level

| Instrument level | Rows |
| --- | --- |
| inter-agency | 18 |
| intergovernmental | 115 |

## Core partner coverage

| Partner | Rows |
| --- | --- |
| Afghanistan (AFG) | 2 |
| Albania (ALB) | 1 |
| Algeria (DZA) | 2 |
| Azerbaijan (AZE) | 6 |
| Bahrain (BHR) | 2 |
| Bangladesh (BGD) | 1 |
| Benin (BEN) | 1 |
| Brazil (BRA) | 1 |
| Burundi (BDI) | 1 |
| Cameroon (CMR) | 2 |
| Chad (TCD) | 1 |
| Chile (CHL) | 1 |
| Cote d'Ivoire (CIV) | 2 |
| Djibouti (DJI) | 2 |
| Ethiopia (ETH) | 4 |
| Gabon (GAB) | 2 |
| Gambia (GMB) | 3 |
| Germany (DEU) | 2 |
| Ghana (GHA) | 1 |
| Guinea (GIN) | 2 |
| Indonesia (IDN) | 1 |
| Italy (ITA) | 1 |
| Jordan (JOR) | 3 |
| Kazakhstan (KAZ) | 2 |
| Kosovo (XKX) | 5 |
| Kuwait (KWT) | 1 |
| Kyrgyzstan (KGZ) | 1 |
| Lebanon (LBN) | 2 |
| Libya (LBY) | 3 |
| Madagascar (MDG) | 2 |
| Maldives (MDV) | 1 |
| Mali (MLI) | 2 |
| Mauritania (MRT) | 1 |
| Mongolia (MNG) | 2 |
| Montenegro (MNE) | 3 |
| Niger (NER) | 3 |
| Nigeria (NGA) | 2 |
| North Macedonia (MKD) | 1 |
| Oman (OMN) | 1 |
| Pakistan (PAK) | 4 |
| Poland (POL) | 2 |
| Portugal (PRT) | 1 |
| Qatar (QAT) | 7 |
| Republic of the Congo (COG) | 1 |
| Romania (ROU) | 2 |
| Rwanda (RWA) | 3 |
| Saudi Arabia (SAU) | 4 |
| Senegal (SEN) | 2 |
| Serbia (SRB) | 1 |
| Slovakia (SVK) | 1 |
| Somalia (SOM) | 4 |
| South Korea (KOR) | 4 |
| Spain (ESP) | 2 |
| Sudan (SDN) | 2 |
| Sweden (SWE) | 1 |
| Tanzania (TZA) | 2 |
| Tunisia (TUN) | 1 |
| Uganda (UGA) | 1 |
| United Arab Emirates (ARE) | 1 |
| United Kingdom (GBR) | 4 |
| United States (USA) | 4 |
| Uzbekistan (UZB) | 3 |

## Extended-only records

| ID | Partner | Actor type | Recognition | Instrument level |
| --- | --- | --- | --- | --- |
| GRP-1506a39d69e2 | Northern Cyprus (XNC) | coast_guard | limited | inter-agency |

## Scope-exception disposition

| Scope status | Rows |
| --- | --- |
| auto_exclude | 7 |
| extended_only | 1 |

The report is generated by `scripts/14_build_validation_report.py`; manual edits to this file will be overwritten.
