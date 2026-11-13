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
