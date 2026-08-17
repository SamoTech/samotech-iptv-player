param(
    [string]$VlcVersion = "3.0.23",
    [string]$OutputRoot = "build/windows"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$zipName = "vlc-$VlcVersion-win64.zip"
$downloadUrl = "https://download.videolan.org/pub/videolan/vlc/$VlcVersion/win64/$zipName"
$expectedSha256 = "992d19dbd0b8a7cde9167d2f7780b1ef6f92acc8a71acfa736101a21f35181e1"
$outputPath = Join-Path $OutputRoot "vlc"
$zipPath = Join-Path $OutputRoot $zipName

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
if (-not (Test-Path $zipPath)) {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath
}
$actualSha256 = (Get-FileHash -Algorithm SHA256 -Path $zipPath).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    throw "VLC SHA256 mismatch: expected $expectedSha256, got $actualSha256"
}

if (Test-Path $outputPath) {
    Remove-Item -Recurse -Force $outputPath
}
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $outputPath -Force
$runtime = Get-ChildItem -Path $outputPath -Directory | Where-Object {
    (Test-Path (Join-Path $_.FullName "libvlc.dll")) -and
    (Test-Path (Join-Path $_.FullName "libvlccore.dll")) -and
    (Test-Path (Join-Path $_.FullName "plugins"))
} | Select-Object -First 1
if ($null -eq $runtime) {
    throw "The downloaded VLC archive did not contain a complete libVLC/plugins tree"
}

$runtime.FullName | Set-Content -Encoding UTF8 (Join-Path $OutputRoot "vlc-root.txt")
Write-Host "VLC runtime prepared: $($runtime.FullName)"
Write-Host "VLC archive SHA256: $actualSha256"
