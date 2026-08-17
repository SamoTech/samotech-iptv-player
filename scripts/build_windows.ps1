param(
    [string]$VlcRoot,
    [string]$DistRoot = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($VlcRoot)) {
    throw "VlcRoot is required"
}
if (-not (Test-Path (Join-Path $VlcRoot "libvlc.dll"))) {
    throw "VlcRoot is missing libvlc.dll"
}
if (-not (Test-Path (Join-Path $VlcRoot "libvlccore.dll"))) {
    throw "VlcRoot is missing libvlccore.dll"
}
if (-not (Test-Path (Join-Path $VlcRoot "plugins"))) {
    throw "VlcRoot is missing the plugins directory"
}

$env:VLC_RUNTIME_DIR = (Resolve-Path $VlcRoot).Path
if (Test-Path $DistRoot) {
    Remove-Item -Recurse -Force $DistRoot
}
$pyinstallerWorkRoot = Join-Path "build" "pyinstaller"
if (Test-Path $pyinstallerWorkRoot) {
    Remove-Item -Recurse -Force $pyinstallerWorkRoot
}

python -m PyInstaller --clean --noconfirm --workpath $pyinstallerWorkRoot samotech-iptv-player.spec
$exe = Join-Path $DistRoot "SamoTech-IPTV-Player-Windows-x64.exe"
if (-not (Test-Path $exe)) {
    throw "PyInstaller did not produce $exe"
}
Write-Host "Built $exe ($((Get-Item $exe).Length) bytes)"
