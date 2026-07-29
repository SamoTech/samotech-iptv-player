# build.ps1 — Build Windows executable via PyInstaller
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Building SamoTech IPTV Player..." -ForegroundColor Cyan
uv run pyinstaller samotech-iptv-player.spec

Write-Host "Build complete. Artifact: dist/" -ForegroundColor Green
