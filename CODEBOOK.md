# TSİAV 2010–2026 codebook

## Dataset unit and coverage

Each row represents one bilateral defence-cooperation legal instrument published
in the Turkish Resmî Gazete. Approval laws and approval decisions that refer to
the same instrument are consolidated into one row while preserving both official
references.

The release covers Resmî Gazete publications from 2010 through the fixed
2026-11-13 snapshot. An agreement may have been signed before 2010 if its Turkish
approval publication falls inside the collection window.

## Release files

- `data/final/tsiav_2010_2026.csv` is the core analytical sample.
- `data/final/tsiav_2010_2026_extended.csv` contains the core sample plus coded
  non-military security-force instruments for robustness checks.
- `data/final/tsiav_pilot_2017.csv` is the manually reviewed regression fixture
  used to test the full pipeline.

## Columns

| Column | Definition |
| --- | --- |
| `id` | Stable row identifier. Generated groups use `GRP-...`; split instruments add a numeric suffix; retained pilot identifiers use `TR-...`. |
| `partner` | Canonical English partner name followed by a three-character country code in parentheses. `XKX` and `XNC` are dataset-specific codes for Kosovo and Northern Cyprus. |
| `title_tr` | Official Turkish instrument title, with Resmî Gazete approval-wrapper language removed. The legal title is not translated. |
| `type` | Primary substantive content code. See the controlled vocabulary below. |
| `is_framework` | `true` exactly when the official Turkish title contains `çerçeve`; otherwise `false`. This flag is independent of `type`. |
| `date_signed` | Signing date in ISO `YYYY-MM-DD` format. If the parties signed on different dates, the later date is stored and both dates are preserved in `notes`. |
| `date_approved` | Approval-decision date when a decision exists; otherwise the law's acceptance date. ISO `YYYY-MM-DD`. |
| `date_in_force` | Reserved for a future systematic entry-into-force pass. Version 1.0.x does not extract this field; it is blank in every released row and must not be interpreted as “never entered into force.” |
| `channel` | Approval-publication channel: `law`, `decision`, or `both`. |
| `law_no` | Turkish approval-law number. Blank when no law publication was identified. Multiple values are semicolon-separated. |
| `decision_no` | Council of Ministers or Presidential approval-decision number. Blank when no decision publication was identified. Multiple values are semicolon-separated. |
| `rg_date` | Resmî Gazete publication date or dates in ISO format. For `both`, law appears before decision. |
| `rg_issue` | Resmî Gazete issue number or numbers, positionally aligned with `rg_date` and `source_url`. |
| `source_url` | Direct official Resmî Gazete URL or URLs. Every released row has at least one official source. |
| `notes` | Documented extraction caveats, multiple signing dates, manual source checks, or split-publication information. |
| `status` | Inclusion status in the released layer. Released rows use `included`. |
| `scope_status` | `confirmed_in` for the core sample and `extended_only` for a coded robustness-layer record. Other statuses occur only in interim review artifacts. |
| `scope_reason` | Human-readable reason for the scope decision. |
| `actor_type` | Actor-family code: `military`, `coast_guard`, `gendarmerie`, or `police`. |
| `partner_recognition` | `un_member` for UN member-state partners and `limited` for limited-recognition partners. This field is descriptive, not an automatic core-sample filter. |
| `instrument_level` | `intergovernmental` when the official title names governments or states as parties; `inter-agency` when it names ministries, general staffs, service commands, academies, or security-force commands without a government party. |
| `core_sample` | Boolean analytical-layer flag. `true` rows form the core release; `false` rows appear only in the extended release. |

Semicolon-separated fields preserve positional order: the first `rg_date`,
`rg_issue`, and `source_url` describe the same publication, as do the second
values, and so on.

## `type` controlled vocabulary

| Code | Meaning |
| --- | --- |
| `training` | Military education, training, student or personnel exchange, or a broader instrument whose main content is training. |
| `defence_industry` | Defence-industry, armaments, military technology, classified defence information, configuration management, or defence-project cooperation. |
| `military_financial` | Military financial assistance, cash assistance, or implementation instruments whose primary content is financial. |
| `protocol_amendment` | Amendment, extension, or modification of an existing defence instrument. |
| `other_military` | Bilateral military content not captured above, including logistics, exercises, host-nation support, health, archives, and personnel exchanges. |
| `framework` | Broad military or defence cooperation with no narrower dominant substantive category. This does not replace `is_framework`. |

An instrument titled, for example, `Askerî Eğitim, Teknik ve Bilimsel İş
Birliği Çerçeve Anlaşması` is coded `type = training` and
`is_framework = true`.

## Scope rules

Core inclusion requires a bilateral defence or military-cooperation instrument
published in the Resmî Gazete. The pipeline searches both approval laws and
approval decisions and deduplicates the two channels.

The core sample excludes:

- domestic regulations and administrative acts;
- police, gendarmerie, coast-guard, customs, and civil-protection-only
  instruments;
- multilateral or three-party instruments;
- NATO or other international-organization agency instruments;
- deployment mandates and operational authorizations that are not bilateral
  cooperation agreements.

Non-military security-force instruments are not deleted. When substantively
useful, they are coded `extended_only` with `core_sample = false`. Limited partner
recognition is recorded separately and does not by itself remove an otherwise
in-scope military agreement from the core sample.

## Missing data and source policy

Unknown values are blank, never inferred. Material gaps are described in
`notes`. Every released row must retain a direct official Resmî Gazete URL.
Manual visual or external official-source corrections are stored in explicit
override files so they can be audited and reproduced.

`date_in_force` is a schema placeholder rather than a populated v1.0.x measure.
It remains in the release to avoid a later breaking column addition, but its
current coverage is 0/133 core rows.

The only missing core signing date in version 1.0 is the Jordan S-70 helicopter
pilot and technician training protocol (`GRP-c7636962ffb6`). Its approval and
publication fields are complete.
