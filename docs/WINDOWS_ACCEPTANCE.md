# Windows Native Acceptance Procedure

## Purpose and boundary

This procedure is the **single final acceptance gate** for native Windows, Qt, and libVLC behavior. It does not replace automated tests. It is to be run only with authorized provider accounts and sources, and it must produce a credential-safe evidence record. Do not paste passwords, MAC identities, tokens, cookies, M3U source URLs, resolved stream URLs, or verbose provider payloads into the resulting log.

The application currently relies on the standard native VLC installation discovered by the `python-vlc` binding. It does not set `VLC_PLUGIN_PATH`, call `os.add_dll_directory`, or implement a custom DLL search path. Consequently, this procedure validates the process-visible Windows installation and treats custom DLL/plugin-path overrides as a remediation target rather than normal configuration.

## Preconditions

Use a 64-bit supported Windows desktop with a user session capable of rendering video and playing audio. Install 64-bit Python 3.12 or newer and a 64-bit VLC distribution. The standard expected installation layout is:

```text
C:\Program Files\VideoLAN\VLC\vlc.exe
C:\Program Files\VideoLAN\VLC\libvlc.dll
C:\Program Files\VideoLAN\VLC\libvlccore.dll
C:\Program Files\VideoLAN\VLC\plugins\
```

Do not mix VLC DLLs, plugins, or `python-vlc` bindings from different VLC installations. Leave `VLC_PLUGIN_PATH` unset for the standard installation. If a custom installation is required, make its architecture and plugin directory explicit in the evidence record and ensure it contains the matching `libvlc.dll`, `libvlccore.dll`, and `plugins` tree.

Create a clean source-install environment from a fresh checkout:

```powershell
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Evidence collection

Run the following PowerShell block before opening the application. Save its output to a local acceptance file with `Tee-Object`; do not include provider credentials in the shell environment or command line.

```powershell
$ErrorActionPreference = 'Stop'
$VlcRoot = Join-Path ${env:ProgramFiles} 'VideoLAN\VLC'
$VlcExe = Join-Path $VlcRoot 'vlc.exe'
$LibVlc = Join-Path $VlcRoot 'libvlc.dll'
$LibVlcCore = Join-Path $VlcRoot 'libvlccore.dll'
$Plugins = Join-Path $VlcRoot 'plugins'
$Log = Join-Path (Get-Location) 'windows-acceptance-environment.txt'

@(
  "Timestamp: $(Get-Date -Format o)",
  "OS: $((Get-CimInstance Win32_OperatingSystem).Caption) $((Get-CimInstance Win32_OperatingSystem).Version)",
  "OS architecture: $((Get-CimInstance Win32_OperatingSystem).OSArchitecture)",
  "Python: $(& python --version)",
  "Python architecture: $(& python -c "import platform; print(platform.architecture()[0])")",
  "VLC root exists: $(Test-Path $VlcRoot)",
  "VLC executable exists: $(Test-Path $VlcExe)",
  "libvlc.dll exists: $(Test-Path $LibVlc)",
  "libvlccore.dll exists: $(Test-Path $LibVlcCore)",
  "plugins directory exists: $(Test-Path $Plugins)",
  "VLC_PLUGIN_PATH set: $([bool]$env:VLC_PLUGIN_PATH)",
  "VLC_PLUGIN_PATH value recorded: $([bool]$env:VLC_PLUGIN_PATH)",
  "python-vlc: $(& python -c "import vlc; print(getattr(vlc, '__version__', 'unknown'))")",
  "PySide6: $(& python -c "import PySide6; print(PySide6.__version__)")",
  "qasync: $(& python -c "import importlib.metadata; print(importlib.metadata.version('qasync'))")"
) | Tee-Object -FilePath $Log

if (Test-Path $VlcExe) { "VLC version: $(& $VlcExe --version | Select-Object -First 1)" | Tee-Object -FilePath $Log -Append }
if (Test-Path $LibVlc) { "libvlc.dll version: $((Get-Item $LibVlc).VersionInfo.FileVersion)" | Tee-Object -FilePath $Log -Append }
if (Test-Path $LibVlcCore) { "libvlccore.dll version: $((Get-Item $LibVlcCore).VersionInfo.FileVersion)" | Tee-Object -FilePath $Log -Append }
if (Test-Path $Plugins) { "Plugin DLL count: $((Get-ChildItem $Plugins -Recurse -Filter '*.dll').Count)" | Tee-Object -FilePath $Log -Append }
Get-ChildItem $env:APPDATA,$env:LOCALAPPDATA -Recurse -Filter 'plugins.dat' -ErrorAction SilentlyContinue |
  ForEach-Object { "Plugin cache: $($_.FullName) modified=$($_.LastWriteTimeUtc.ToString('o'))" } |
  Tee-Object -FilePath $Log -Append
Get-ChildItem Env:VLC* | ForEach-Object { "VLC environment variable present: $($_.Name)" } |
  Tee-Object -FilePath $Log -Append
```

The evidence output intentionally records only whether `VLC_PLUGIN_PATH` is set, not its path. A custom path may contain sensitive local information and must be reviewed locally.

## Native initialization and quality gate

Run the deterministic checks before live provider validation:

```powershell
black --check src tests providers
ruff check src tests providers
mypy src
pytest -q
python -c "import vlc; instance = vlc.Instance(); player = instance.media_player_new(); player.release(); instance.release(); print('native libVLC initialization: PASS')"
```

A failure from the final command is a native-runtime failure. Capture only the exception type and the DLL/plugin facts above. Do not claim playback success from Python import success alone.

## Live acceptance sequence

Start the desktop application with credential-safe diagnostics enabled:

```powershell
$env:IPTV_DEBUG = '1'
samotech-iptv
```

Enter each authorized source interactively through the application. Do not redirect the console output to an artifact until it has been reviewed for secret-bearing values. The application is expected to log only redacted diagnostic metadata, but human review remains mandatory.

| Order | Acceptance action | Pass criterion | Evidence to record |
|---:|---|---|---|
| 1 | Complete the native libVLC initialization command. | A real instance and media player are created and released. | PASS/FAIL and safe environment facts. |
| 2 | Register or select the authorized M3U provider, then load channels. | The channel list loads without session errors. | Channel count and failure category only. |
| 3 | Select an M3U live channel and invoke registered stream resolution. | Resolution completes through the registered-provider workflow. | PASS/FAIL only; never the URL. |
| 4 | Play the selected M3U channel. | Video, audio, and Qt responsiveness are observed. | PASS/FAIL, elapsed startup time, and safe failure category. |
| 5 | Register or select the authorized Xtream provider and authenticate. | Authentication completes. | PASS/FAIL only. |
| 6 | Load Xtream live categories and channels. | Categories and live channels load without a translation-wide failure. | Counts and rejected-record count only. |
| 7 | Resolve and play one Xtream live channel. | Resolution, video, audio, and UI responsiveness succeed. | PASS/FAIL and safe failure category. |
| 8 | Stop the active channel and play it again. | Stop/replace/replay performs without stale video, audio, or UI lockup. | PASS/FAIL. |
| 9 | Rapidly select three distinct channels. | The last selection is the only visible/audible stream; stale callbacks do not change UI state. | PASS/FAIL. |
| 10 | Attempt a known controlled dead-stream case. | A generic UI failure occurs without freezing the application or exposing the stream URL. | Classified failure and recovery result. |
| 11 | Repeat one live playback with hardware decoding enabled, then with software fallback. | Each observed result is recorded independently; no fallback is inferred solely from a log line. | Hardware and software results separately. |

Test MAG/Stalker separately. Its real production portal/profile state remains unresolved until an authorized trace proves a concrete server path and handshake profile. Do not fabricate tokens, bypass authentication, or automatically guess profiles.

## VLC plugin-cache remediation

The following messages alone do not prove an application defect: references to stale plugin modules such as `libglwin32_plugin.dll`, `libwgl_plugin.dll`, or visualization/video-output modules may be emitted while VLC rebuilds a cache. Classify the result using the sequence below.

| Observation | Classification | Required action |
|---|---|---|
| Native initialization and live playback both succeed; cache messages cease or are non-fatal. | Harmless cache regeneration. | Record the result; do not change application code. |
| Standard 64-bit VLC is installed, `VLC_PLUGIN_PATH` is unset, but cache messages recur and native initialization fails. | Suspected damaged or mixed VLC installation. | Reinstall one matching 64-bit VLC distribution; do not copy DLLs manually. Re-run evidence collection. |
| `VLC_PLUGIN_PATH` is set or points outside the matching VLC root. | Incorrect override or mixed plugin path. | Remove the override for the standard installation, restart PowerShell, and re-run. |
| `libvlc.dll`, `libvlccore.dll`, or `plugins` are missing, or their bitness/version differs. | Installation or architecture mismatch. | Install a matching 64-bit VLC and use matching 64-bit Python. |
| Python imports `vlc` but `vlc.Instance()` fails. | Binding/native-DLL boundary failure. | Record exception type and environment facts; resolve installation/path mismatch before investigating application playback code. |

If a cache reset is necessary after correcting the installation, close VLC and the application, preserve the current evidence record, and use the VLC installer’s repair/reinstall path first. Do not delete caches or plugins blindly. If local policy permits a manual cache reset, record the exact path and timestamp separately; never add that user-specific path to committed source files.

## Completion record

Record each row as **VERIFIED**, **SIMULATED**, **PENDING**, **UNRESOLVED**, **NOT IMPLEMENTED**, or **ENVIRONMENT LIMITATION**. A native playback claim requires observed Windows video and audio with real libVLC. No result from Linux, a fake backend, or a Python binding import can substitute for that evidence.

The acceptance run is complete only when the environment facts, native initialization result, M3U live path, Xtream live path, stop/replay, rapid switching, dead-stream recovery, and hardware/software observations are recorded. The exact next action after a non-Windows audit is to run this procedure on a matching Windows desktop with authorized test sources.
