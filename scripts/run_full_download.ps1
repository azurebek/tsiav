param(
    [int]$StartYear = 2010,
    [int]$EndYear = 2026,
    [string]$Through = "2026-10-27",
    [double]$Delay = 2.3
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

for ($year = $StartYear; $year -le $EndYear; $year++) {
    Write-Output "=== Starting year $year at $(Get-Date -Format o) ==="
    & python "scripts\01_download_index.py" `
        --year $year `
        --through $Through `
        --delay $Delay
    if ($LASTEXITCODE -ne 0) {
        throw "Index download failed for year $year with exit code $LASTEXITCODE"
    }
    Write-Output "=== Finished year $year at $(Get-Date -Format o) ==="
}

Write-Output "=== Full index download completed at $(Get-Date -Format o) ==="
