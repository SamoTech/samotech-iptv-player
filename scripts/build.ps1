param(
    [string]$VlcRoot = $env:VLC_RUNTIME_DIR
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "build_windows.ps1") -VlcRoot $VlcRoot
