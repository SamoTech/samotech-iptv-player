@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Optional local launcher for safe startup and playback lifecycle diagnostics.
rem It never accepts, prints, or stores provider credentials or private URLs.
set "SCRIPT_DIR=%~dp0"
set "APP_EXE="
for %%F in ("%SCRIPT_DIR%SamoTech-IPTV-Player-Windows-x64*.exe") do (
  if exist "%%~fF" set "APP_EXE=%%~fF"
)

if not defined APP_EXE (
  echo [SamoTech Debug] Portable EXE not found beside this launcher.
  exit /b 2
)

if not defined SAMOTECH_STARTUP_DIAGNOSTIC_PATH (
  set "SAMOTECH_STARTUP_DIAGNOSTIC_PATH=%TEMP%\samotech-startup-diagnostic.json"
)

echo [SamoTech Debug] Starting local diagnostic session
echo [SamoTech Debug] Startup diagnostics: %SAMOTECH_STARTUP_DIAGNOSTIC_PATH%
echo [SamoTech Debug] Console events are sanitized; credentials and private URLs are never displayed.
"%APP_EXE%" --diagnostic %*
set "EXIT_CODE=%ERRORLEVEL%"
echo [SamoTech Debug] Application exit code: %EXIT_CODE%

if /I not "%SAMOTECH_DEBUG_NO_PAUSE%"=="1" pause
exit /b %EXIT_CODE%
