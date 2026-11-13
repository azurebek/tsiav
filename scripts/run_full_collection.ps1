param(
    [int]$StartYear = 2010,
    [int]$EndYear = 2026,
    [Parameter(Mandatory = $true)]
    [string]$Through,
    [double]$Delay = 2.3
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

Write-Output "=== Updating indexes through $Through ==="
& powershell -ExecutionPolicy Bypass -File "scripts\run_full_download.ps1" `
    -StartYear $StartYear `
    -EndYear $EndYear `
    -Through $Through `
    -Delay $Delay
if ($LASTEXITCODE -ne 0) {
    throw "Index update failed with exit code $LASTEXITCODE"
}

Write-Output "=== Filtering $StartYear-$EndYear indexes ==="
& python "scripts\02_filter.py" `
    --start-year $StartYear `
    --end-year $EndYear `
    --output "data\interim\candidates_full.csv"
if ($LASTEXITCODE -ne 0) {
    throw "Candidate filtering failed with exit code $LASTEXITCODE"
}

Write-Output "=== Fetching candidate documents ==="
& python "scripts\03_fetch_docs.py" `
    --input "data\interim\candidates_full.csv" `
    --output "data\raw\docs" `
    --failures "data\interim\download_failures.csv" `
    --delay $Delay
if ($LASTEXITCODE -ne 0) {
    throw "Document download failed with exit code $LASTEXITCODE"
}

Write-Output "=== Extracting candidate document text ==="
& python "scripts\04_extract.py" `
    --candidates "data\interim\candidates_full.csv" `
    --docs "data\raw\docs" `
    --output "data\interim\extracted_docs_full.json"
if ($LASTEXITCODE -ne 0) {
    throw "Document extraction failed with exit code $LASTEXITCODE"
}

Write-Output "=== Full collection stage completed at $(Get-Date -Format o) ==="
