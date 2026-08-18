param(
    [ValidateSet("onedir", "onefile", "debug-bootloader", "debug-all")]
    [string]$Mode,
    [Parameter(Mandatory = $true)]
    [string]$VlcRoot,
    [string]$DistRoot = "dist\forensic",
    [string]$RuntimeTmpDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedVlcRoot = (Resolve-Path $VlcRoot).Path
foreach ($required in @("libvlc.dll", "libvlccore.dll", "plugins")) {
    if (-not (Test-Path (Join-Path $resolvedVlcRoot $required))) {
        throw "VlcRoot is missing $required"
    }
}

$modeRoot = Join-Path $DistRoot $Mode
$workRoot = Join-Path "build\pyinstaller-forensic" $Mode
if (Test-Path $modeRoot) {
    Remove-Item -Recurse -Force $modeRoot
}
if (Test-Path $workRoot) {
    Remove-Item -Recurse -Force $workRoot
}
New-Item -ItemType Directory -Force -Path $modeRoot | Out-Null

$env:VLC_RUNTIME_DIR = $resolvedVlcRoot
$env:SAMOTECH_FORENSIC_BUILD_MODE = $Mode
if ([string]::IsNullOrWhiteSpace($RuntimeTmpDir)) {
    Remove-Item Env:SAMOTECH_FORENSIC_RUNTIME_TMPDIR -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Force -Path $RuntimeTmpDir | Out-Null
    $env:SAMOTECH_FORENSIC_RUNTIME_TMPDIR = (Resolve-Path $RuntimeTmpDir).Path
}

python -m PyInstaller --clean --noconfirm --workpath $workRoot --distpath $modeRoot packaging\samotech_forensic.spec

$expectedExe = Join-Path $modeRoot "SamoTech-IPTV-Player-Windows-x64-forensic-$Mode.exe"
if ($Mode -eq "onedir") {
    $expectedExe = Join-Path $modeRoot "SamoTech-IPTV-Player-Windows-x64-forensic-onedir.exe"
    if (-not (Test-Path $expectedExe)) {
        $expectedExe = Get-ChildItem -Path $modeRoot -Filter "SamoTech-IPTV-Player-Windows-x64-forensic-onedir.exe" -File -Recurse |
            Select-Object -First 1 -ExpandProperty FullName
    }
}
if ([string]::IsNullOrWhiteSpace($expectedExe) -or -not (Test-Path $expectedExe)) {
    throw "Forensic build did not produce expected executable: $expectedExe"
}

$metadata = @(
    "mode=$Mode",
    "vlc_root=$resolvedVlcRoot",
    "runtime_tmpdir=$RuntimeTmpDir",
    "executable=$expectedExe",
    "size_bytes=$((Get-Item $expectedExe).Length)",
    "sha256=$((Get-FileHash -Algorithm SHA256 $expectedExe).Hash.ToLowerInvariant())"
)
$metadata | Set-Content -Encoding utf8 (Join-Path $modeRoot "forensic-build-metadata.txt")
$metadata | Write-Output
