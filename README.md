# SamoTech IPTV Player

> A provider-agnostic IPTV desktop player for authorized sources.

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/codeql.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/codeql.yml)
[![Windows Portable Build](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/windows-portable-build.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/windows-portable-build.yml)
[![Latest release](https://img.shields.io/github/v/release/SamoTech/samotech-iptv-player?display_name=tag&sort=semver)](https://github.com/SamoTech/samotech-iptv-player/releases)
[![License](https://img.shields.io/github/license/SamoTech/samotech-iptv-player)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows x64](https://img.shields.io/badge/platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://github.com/SamoTech/samotech-iptv-player/releases)
[![Sponsor SamoTech](https://img.shields.io/badge/Sponsor-SamoTech-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/SamoTech)

SamoTech IPTV Player connects authorized IPTV sources through isolated provider adapters, converts provider responses into canonical records, resolves supported streams, and sends them to a shared PySide6/libVLC desktop player. Credentials and provider sessions stay inside secure infrastructure boundaries.

## Download

Download the current Windows portable build from the [GitHub Releases page](https://github.com/SamoTech/samotech-iptv-player/releases). The release page is the only supported download location. Review the release notes and checksums before use.

## Current scope

| Area | Status |
|---|---|
| M3U | Local, file, and HTTP(S) playlists; validated parsing; live-channel browsing; supported HTTP(S) playback. |
| Xtream Codes | Credential validation; account and server metadata; Live, VOD, Series, Seasons, Episodes, categories, short EPG, local search, and supported stream resolution. |
| MAG/Stalker | Authorized MAC identity; bounded handshake discovery; session lifecycle; Live TV, EPG, local search, and live stream resolution. |
| Desktop player | PySide6 shell, shared libVLC playback, pause/resume/stop, recording, themes, provider management, favorites, history, and safe diagnostics. |

**Compatibility is evidence-based.** Deterministic tests prove the supported application boundaries. They do not prove that every provider, portal, catalogue, stream, or consumer machine is compatible. Populated authorized Xtream acceptance and authorized production MAG/Stalker acceptance remain separate runtime gates.

## Install from source

Python **3.12 or newer** and a compatible VLC/libVLC runtime are required for source execution. The supported source platforms are Linux, macOS, and Windows. The portable release target is Windows x64.

```bash
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
python -m venv .venv

# Linux/macOS
. .venv/bin/activate

# Windows PowerShell
. .venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
```

Run the application with:

```bash
samotech-iptv
# or
python -m samotech_iptv
```

The default application-data locations are platform appropriate. Set `IPTV_DATA_DIR` to use an explicit location. `python-vlc` provides the Python binding; it does not install libVLC.

## Development checks

The repository uses deterministic fixtures and authorized-source boundaries. Run the blocking local checks before committing:

```bash
ruff check src/ tests/ providers/ scripts/
black --check src/ tests/ providers/
mypy src/
python -m pip check
python -m compileall -q src providers tests

files=$(find tests -type f -name 'test_*.py' ! -name 'test_presentation_*.py' | sort)
QT_QPA_PLATFORM=offscreen PYTHONPATH=src pytest -q $files
python -m build
git diff --check
```

The full Windows packaging workflow is separate from Linux testing. It validates the packaged runtime, native Qt startup, VLC runtime discovery, release metadata, and location/path scenarios on Windows.

## Security

Use authorized provider sources only. Do not commit usernames, passwords, MAC identities, session tokens, cookies, signed URLs, private stream URLs, or production logs. Credentials are stored through the operating-system keyring; provider metadata remains non-secret; session state stays in volatile provider adapters; and user-facing errors are generic.

Automatic provider detection is local and bounded. The application does not act as an open provider scanner, proxy, credential forwarder, or CORS relay.

## Architecture

```text
Authorized source
    ↓
Provider adapter and protocol DTOs
    ↓
Validation and canonical domain records
    ↓
Application use cases and typed ports
    ↓
Resolved playback target
    ↓
PlayerPort → shared libVLC backend
    ↓
PySide6 desktop presentation
```

The main packages are `domain`, `application`, `infrastructure`, and `presentation`. Provider-specific protocol details do not cross into the presentation layer.

## Documentation

The most relevant project records are [PROJECT_STATUS.md](PROJECT_STATUS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), and the [provider and UI evidence audit](docs/evidence/NEXT_PHASE_PROVIDER_UI_AUDIT.md).

## License

MIT. See [LICENSE](LICENSE).

## Support

If this project is useful, support continued development through [GitHub Sponsors](https://github.com/sponsors/SamoTech).
