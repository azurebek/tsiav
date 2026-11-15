$ErrorActionPreference = "Stop"

function Invoke-PythonStep {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python step failed: python $($Arguments -join ' ')"
    }
}

Invoke-PythonStep scripts/05_prepare_review.py
Invoke-PythonStep scripts/06_deduplicate.py
Invoke-PythonStep scripts/07_audit_dedup.py --threshold 0.72
Invoke-PythonStep scripts/08_extract_publication_fields.py
Invoke-PythonStep scripts/09_ocr_missing_publications.py
Invoke-PythonStep scripts/08_extract_publication_fields.py
Invoke-PythonStep scripts/06_deduplicate.py --start-year 2017 --end-year 2017 --groups tmp/groups_2017.csv --members tmp/members_2017.csv
Invoke-PythonStep scripts/10_validate_pilot.py
Invoke-PythonStep scripts/11_build_provisional_dataset.py
Invoke-PythonStep scripts/12_finalize_publication_review.py
Invoke-PythonStep scripts/12_materialize_review_outputs.py
Invoke-PythonStep scripts/13_validate_full_draft.py
Invoke-PythonStep scripts/14_build_validation_report.py
