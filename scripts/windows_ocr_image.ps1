param(
    [Parameter(Mandatory = $true)]
    [string]$ImagePath,
    [string]$Language = "tr"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
        $_.Name -eq "AsTask" -and
        $_.IsGenericMethod -and
        $_.GetParameters().Count -eq 1
    } |
    Select-Object -First 1

function Await-WinRt {
    param(
        [Parameter(Mandatory = $true)]$Operation,
        [Parameter(Mandatory = $true)][Type]$ResultType
    )

    $method = $asTaskGeneric.MakeGenericMethod($ResultType)
    $task = $method.Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}

$resolvedPath = (Resolve-Path -LiteralPath $ImagePath).Path
$file = Await-WinRt (
    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]::GetFileFromPathAsync($resolvedPath)
) ([Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime])
$stream = Await-WinRt (
    $file.OpenAsync([Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime]::Read)
) ([Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime])
$decoder = Await-WinRt (
    [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]::CreateAsync($stream)
) ([Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime])
$bitmap = Await-WinRt (
    $decoder.GetSoftwareBitmapAsync()
) ([Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType = WindowsRuntime])

$recognizerLanguage = New-Object 'Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime'($Language)
$engine = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]::TryCreateFromLanguage($recognizerLanguage)
if ($null -eq $engine) {
    throw "No Windows OCR engine is available for language '$Language'."
}
$result = Await-WinRt (
    $engine.RecognizeAsync($bitmap)
) ([Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType = WindowsRuntime])
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$result.Text
