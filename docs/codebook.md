# TSİAV pilot codebook

The unit of observation is one bilateral defence cooperation agreement published
in the Resmî Gazete. A law and an approval decision referring to the same
agreement are merged into one record and both references are retained.

## Types

- `type` records the agreement's main substantive content. Structural wording in
  the title does not override that content. For example, an `Askerî Eğitim, Teknik
  ve Bilimsel İş Birliği Çerçeve Anlaşması` is coded `training`.
- `framework`: military framework or general military cooperation.
- `training`: military education, technical, or scientific cooperation.
- `defence_industry`: defence-industry cooperation.
- `military_financial`: military financial cooperation or cash assistance.
- `protocol_amendment`: a protocol implementing or amending an earlier agreement.
- `other_military`: military cooperation not fitting the categories above.

## Framework flag

- `is_framework` is `true` when the official Turkish title contains the word
  `çerçeve`; otherwise it is `false`.
- This flag is independent of `type`. An agreement can therefore have
  `type = training` and `is_framework = true` at the same time.

Unknown values are stored as null and explained in `notes`. No included record
may lack a Resmî Gazete source URL.
