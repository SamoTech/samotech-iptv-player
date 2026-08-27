# SamoTech IPTV Player

> **A provider-agnostic IPTV desktop player and media-platform foundation for authorized sources.**

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/codeql.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/codeql.yml)
[![Windows Portable EXE](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/windows-portable-build.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/windows-portable-build.yml)
[![Latest release](https://img.shields.io/github/v/release/SamoTech/samotech-iptv-player?display_name=tag&sort=semver)](https://github.com/SamoTech/samotech-iptv-player/releases)
[![Release downloads](https://img.shields.io/github/downloads/SamoTech/samotech-iptv-player/total?label=release%20downloads)](https://github.com/SamoTech/samotech-iptv-player/releases)
[![v0.1.1 downloads](https://img.shields.io/github/downloads/SamoTech/samotech-iptv-player/v0.1.1/total?label=v0.1.1%20downloads)](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.1)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=SamoTech.samotech-iptv-player)](https://github.com/SamoTech/samotech-iptv-player)
[![Stars](https://img.shields.io/github/stars/SamoTech/samotech-iptv-player?style=social)](https://github.com/SamoTech/samotech-iptv-player/stargazers)
[![Forks](https://img.shields.io/github/forks/SamoTech/samotech-iptv-player?style=social)](https://github.com/SamoTech/samotech-iptv-player/network/members)
[![License](https://img.shields.io/github/license/SamoTech/samotech-iptv-player)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows x64](https://img.shields.io/badge/platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://github.com/SamoTech/samotech-iptv-player/releases)
[![Sponsor SamoTech](https://img.shields.io/badge/Sponsor-SamoTech-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/SamoTech)

SamoTech IPTV Player connects authorized IPTV sources through isolated provider adapters, translates provider responses into canonical domain records, resolves supported media streams, and presents them through a PySide6/Qt desktop shell backed by libVLC. Provider protocols remain separate from application use cases, player contracts, persistence, and presentation code.

## Current evidence at a glance

| Area | Current evidence |
|---|---|
| Latest published release | [`v0.1.4`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.4), Windows x64 portable EXE and SHA256 manifest |
| Exact release acceptance | The published `v0.1.4` EXE passed **48/48** executions across six locations, normal and sanitized PATH, first/second launch, packaged-VLC smoke, and Qt smoke in [run 32143064567][4] |
| Security logging | Central pre-logger redaction, canary regression tests, blocking CI gate, and CodeQL closure evidence for the High-severity logging findings in [the security audit][5] |
| Windows incident status | **v0.1.3 root cause PROVEN; v0.1.4 hosted-Windows acceptance PASS.** The original real Windows 11 client was not re-tested; see [the protocol/playback architecture](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md) and [the forensic audit][6] |
| Architecture | Clean Architecture boundaries across domain, application, infrastructure, presentation, provider adapters, and `PlayerPort`/libVLC |
| License | MIT |

> **Important:** Passing CI or hosted-Windows acceptance does not prove universal consumer-Windows compatibility, SmartScreen reputation, populated real-provider compatibility, or acceptance on the original Windows 11 client. Read the [protocol/playback architecture](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md) for the current evidence boundaries.

## What the application provides

SamoTech is designed around canonical records for channels, categories, streams, movies, series, seasons, episodes, EPG entries, favorites, history, and settings. Provider-specific credentials, sessions, and protocol payloads remain in infrastructure adapters; the rest of the application communicates through stable domain records and typed ports.

| Capability | Status and scope |
|---|---|
| Provider registration | Credential-safe registration and management for M3U, Xtream Codes, and MAG/Stalker profiles; Smart Import supports a local Paste → Detect → Review → Validate → Add flow. |
| Live TV | Canonical live-channel browsing, local search, provider-scoped stream resolution, native video-surface attachment, and libVLC playback orchestration where the provider contract supports it. |
| Movies and VOD | Xtream Movie catalogue/detail loading, local category/search/sort controls, metadata display, favorites, and shared `ResolvedPlayback` → `PlayerPort` → libVLC handoff. |
| Series and episodes | Xtream Series → Season → Episode discovery, local filtering and search, provider-scoped identity protection, and Episode playback through the shared player path. |
| EPG | MAG/Stalker and Xtream adapter EPG plus bounded XMLTV parsing for explicit local/file mappings and manual refresh. Scheduled remote XMLTV, caching, catch-up linkage, and archive playback remain deferred. |
| Player | libVLC play, pause, resume, stop, native video output, local MPEG-TS recording, bounded live EOF/STOPPED/EncounteredError recovery, safe provider/content/transport telemetry, and guarded local subtitle attachment for SRT, ASS, SSA, and VTT. |
| Libraries | SQLite-backed Favorites and bounded History with provider-scoped identities, recency, duration, playback-position display, refresh, and protected clear-all. |
| Desktop shell | PySide6 dialogs and views, qasync runtime integration, theme settings, provider health summaries, global search filters, Smart Import, and one shared libVLC player. |
| Extensibility | Explicitly trusted local Python provider-plugin SDK with API-version, identity, and namespace validation. |

## Provider and source compatibility

“Implemented” means the boundary is executable and tested at the stated layer. It does not imply that every provider, portal, catalogue, network, or consumer environment is compatible.

| Provider/source | Status | Current evidence | Explicit limitation |
|---|---|---|---|
| Extended M3U | **Partially implemented** | Local/file/HTTP(S) loading, extended-M3U parsing, escaped-attribute handling, canonical live channels, supported HTTP(S) stream resolution, and evidence-backed User-Agent/Referer transport metadata. | Cookie/arbitrary-header propagation, VOD/series UI, and non-HTTP(S) playback remain outside the current contract. |
| Xtream Codes API | **Partially implemented** | Credential validation, account metadata, live categories/channels, VOD and Series structures, Movie details, Episode discovery, short EPG, local search, filters, sorting, artwork, and shared playback resolution. | Populated authorized real VOD/Series acceptance and broader provider quirks remain unverified; no credentials are stored in this repository. |
| MAG/Stalker | **Partially implemented / provider-specific** | MAC identity handling, bounded handshake candidates, explicit session lifecycle, legacy/Stalker-query/GUI/helper request profiles, live channels, EPG, local search, and local source-derived protocol laboratory. | No authorized production portal produced a verified token-bearing handshake in the documented validation; VOD/Series/catch-up are not claimed. |
| Ministra | **Compatibility investigation** | Public protocol research, source inspection, and deterministic local middleware laboratory. | The authorized portal family, version, routing, and authorization policy remain unidentified; no dedicated production adapter is claimed. |
| Trusted local plugins | **Implemented** | Explicit local loading, API/namespace validation, transactional registration, and reference-plugin coverage. | No remote marketplace, auto-discovery, signing, or remote installation. |

## Playlist, manifest, and transport scope

| Technology | Status | Scope |
|---|---|---|
| Extended M3U | Implemented at parser/source boundary | Metadata and stream URI parsing into canonical records. |
| M3U8/HLS | Partially implemented | Bounded manifest metadata parsing; adaptive playback is delegated to libVLC. |
| MPEG-DASH MPD | Partially implemented | Bounded live/VOD and representation metadata parsing; no Python adaptive engine. |
| XMLTV | Partially implemented | Safe bounded parsing for explicit source-channel mappings and local/file refresh. |
| HTTP(S) | Partially implemented | URI validation/classification and provider-resolved playback through libVLC. |
| RTMP(S), RTSP, UDP, RTP, SRT | Classified, not fully negotiated | URI classification exists; no dedicated transport UX or application-level capability negotiation. |

## Architecture

```text
Authorized IPTV provider or source
        ↓
Provider adapter and protocol DTOs
        ↓
Infrastructure translation and validation
        ↓
Canonical domain entities and value objects
        ↓
Application use cases and typed ports
        ↓
Authorized stream resolution
        ↓
PlayerPort → shared libVLC backend
        ↓
PySide6/Qt desktop presentation
```

The `domain` package contains framework-independent records and validation. The `application` package orchestrates use cases through abstract ports. The `infrastructure` package owns provider adapters, parsers, SQLite, OS-keyring storage, networking, plugins, and libVLC. The `presentation` package owns PySide6 views, dialogs, widgets, native video output, and themes. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Installation from source

The source application requires **Python 3.12 or newer**. The supported source-runtime platforms are Linux, macOS, and Windows where PySide6 and a compatible VLC/libVLC runtime are available. The supported portable release target is Windows x64. Runtime dependencies include `aiohttp`, `defusedxml`, `keyring`, `python-vlc`, `PySide6`, and `qasync`.

Application settings and the local SQLite database use the platform application-data convention by default: `%LOCALAPPDATA%\\SamoTech\\IPTV Player` on Windows, `~/Library/Application Support/SamoTech/IPTV Player` on macOS, and `$XDG_DATA_HOME/SamoTech/IPTV Player` or `~/.local/share/SamoTech/IPTV Player` on Linux. Set `IPTV_DATA_DIR` when an explicit location is required.

```bash
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
python -m venv .venv

# Linux/macOS
. .venv/bin/activate

# Windows PowerShell
. .venv\Scripts\Activate.ps1

pip install -e '.[dev]'
```

A normal library installation is also supported:

```bash
pip install .
```

For source execution, the operating system must provide libVLC. `python-vlc` is a Python binding, not a VLC runtime installer. The application performs guarded libVLC initialization before constructing the main window; if the native runtime is absent or misconfigured, it exits with a generic safe message and writes sanitized troubleshooting details to the startup diagnostic path.

### Clean installation and reproducible build

From a clean Python 3.12+ environment, run:

```bash
python -m venv .venv-clean
python -m pip install --upgrade pip
python -m pip install .
python -m pip check
python -m compileall -q .
python -m pip install --upgrade build
python -m build
```

For development and tests, install the optional development dependencies with `python -m pip install -e '.[dev]'`. Then run `pytest -q`; the normal unit and integration corpus uses deterministic fixtures and does not require a live IPTV provider or stream. The PySide6 presentation tests and native probes require an offscreen-capable Qt runtime. Real VLC/live-stream checks are integration-only and require an authorized source and a locally installed or bundled VLC runtime.

## Running the application

After installation, use either supported entry point:

```bash
samotech-iptv
# equivalent:
python -m samotech_iptv
```

The entry point composes safe local state, restores registered provider metadata, loads the persisted theme, starts the qasync runtime, shares one libVLC player, and closes the shared HTTP resource when the window exits. Startup errors are reported generically so provider information is not exposed.

## Windows portable release

The [Windows Portable EXE workflow](.github/workflows/windows-portable-build.yml) builds a single-file Windows x64 executable with Python, PySide6, `python-vlc`, Qt runtime components, libVLC, libVLCcore, and the VLC plugin tree bundled into the artifact. End users do not need a separate Python, PySide6, `python-vlc`, or VLC installation for the packaged runtime contract. The exact published v0.1.4 artifact passed the release acceptance matrix, while the current provider/media-plane boundaries and real-provider limitations are documented in [PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md).

The current release is [`v0.1.4`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.4). Download the executable and its checksum manifest from the [GitHub Release page](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.4). The release asset is independently verified by [Windows Release Artifact Acceptance run 32143064567][4], which executes the exact published asset rather than only a freshly built workspace copy.

The permanent acceptance workflow checks:

- SHA256 and `SHA256SUMS.txt` integrity;
- PE FileVersion and ProductVersion against the release tag;
- packaged VLC smoke and Qt/application smoke;
- C-drive, temporary, spaces, Unicode, Downloads-like, and arbitrary-CWD locations;
- normal and sanitized PATH; and
- first and second launches with explicit exit-code and timeout checks.

The exact `v0.1.4` artifact passed all **48/48** executions in the expanded hosted-Windows matrix. This does not establish SmartScreen reputation, Authenticode signing, ARM64 support, consumer antivirus behavior, populated real-provider compatibility, or full manual GUI/provider acceptance. See [WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md](WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md), [PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md), and [ZERO_TOUCH_WINDOWS_RELEASE_AUDIT.md](ZERO_TOUCH_WINDOWS_RELEASE_AUDIT.md).

## Security model

Provider credentials, MAC identities, session tokens, authorization headers, cookies, signed URLs, and resolved playback URLs are sensitive. Credentials are owned by the OS keyring; SQLite stores non-secret provider metadata; tokens and session state remain inside runtime adapters; and Qt dialogs display only safe summaries and generic errors.

Sensitive diagnostic data is sanitized **before** it reaches the logger through the central [`safe_logging`](src/samotech_iptv/core/safe_logging.py) APIs. The repository includes canary regression tests, an artifact-output audit, blocking CI security tests, and CodeQL analysis. The complete remediation record is in [SECURITY_CODEQL_LOGGING_REMEDIATION_AUDIT.md](SECURITY_CODEQL_LOGGING_REMEDIATION_AUDIT.md).

Do not commit credentials, tokens, private provider URLs, authorized MAC addresses, raw provider payloads, or captured production logs. Use synthetic test fixtures only. See [SECURITY.md](SECURITY.md) and [docs/m3u_secure_source_design.md](docs/m3u_secure_source_design.md).

## Quality and acceptance evidence

Run the local quality gate before committing:

```bash
ruff check src/ tests/ providers/ scripts/
black --check src/ tests/ providers/
mypy src/

files=$(find tests -type f -name 'test_*.py' ! -name 'test_presentation_*.py' | sort)
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  pytest -q --cov=src --cov-report=xml $files

git diff --check
```

The repository’s CI runs the offscreen PySide6 probes, Ruff, Black, mypy, blocking security regression tests, and the non-presentation corpus. The native PlayerShell probe currently passes **17/17** checks, and the performance probe covers local catalogues from 10K through 100K records. The hosted Windows artifact gate is separate because Linux cannot execute the Windows PE directly.

The known fatal Qt presentation-test collection crash is intentionally excluded from the Ubuntu broad corpus through `test_presentation_*.py`; the exclusion is regression-tested and does not weaken the blocking security gate.

## Project structure

```text
src/samotech_iptv/
├── domain/          Canonical IPTV records, value objects, and interfaces
├── application/     Use cases, DTOs, and abstract provider/player ports
├── infrastructure/  Adapters, parsers, SQLite, keyring, networking, VLC, plugins
├── presentation/    PySide6 dialogs, views, widgets, and theme engine
├── desktop_bootstrap.py
├── desktop_composition.py
└── desktop_runtime.py
providers/           Legacy MAG provider implementation behind the adapter
plugins/             Reference trusted local provider plugin
.github/workflows/   CI, CodeQL, packaged Windows build, exact-release acceptance
```

## Documentation and audit trail

| Document | Purpose |
|---|---|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current implementation matrix and known limitations |
| [ROADMAP.md](ROADMAP.md) | Delivery sequence and next milestones |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Clean Architecture and runtime composition |
| [docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md) | Current M3U, Xtream, MAG/Stalker, control/media plane, libVLC, buffering, recovery, and KiddaC comparison |
| [IPTVNATOR_INFORMED_PLAYBACK_RELIABILITY_IMPLEMENTATION_AUDIT.md](IPTVNATOR_INFORMED_PLAYBACK_RELIABILITY_IMPLEMENTATION_AUDIT.md) | Authoritative Phase 3 IPTVnator-informed implementation and validation audit |
| [SECURITY.md](SECURITY.md) | Security policy and safe-diagnostics rules |
| [SECURITY_CODEQL_LOGGING_REMEDIATION_AUDIT.md](SECURITY_CODEQL_LOGGING_REMEDIATION_AUDIT.md) | Sensitive-logging remediation and CodeQL evidence |
| [WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md](WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md) | Authoritative v0.1.3/v0.1.4 Windows silent-exit investigation |
| [ZERO_TOUCH_WINDOWS_RELEASE_AUDIT.md](ZERO_TOUCH_WINDOWS_RELEASE_AUDIT.md) | Windows build/release pipeline evidence |
| [REAL_WORLD_IPTV_COMMERCIAL_VALIDATION_AUDIT.md](REAL_WORLD_IPTV_COMMERCIAL_VALIDATION_AUDIT.md) | Commercial reliability validation and limitations |
| [COMMERCIAL_SUBTITLE_FINAL_AUDIT.md](COMMERCIAL_SUBTITLE_FINAL_AUDIT.md) | Provider health, search, subtitle, and playback hardening evidence |
| [SMART_IMPORT_FINAL_AUDIT.md](SMART_IMPORT_FINAL_AUDIT.md) | Smart Import implementation and verification |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow and quality expectations |

## Roadmap and known limitations

The project is intentionally evidence-driven. The remaining high-value work includes populated authorized-provider acceptance, broader MAG/Ministra portal compatibility, full manual Windows GUI acceptance, SmartScreen/code-signing strategy, ARM64 packaging, installer/update distribution, richer XMLTV scheduling and catch-up, and provider-neutral archive playback.

The published v0.1.3 Windows silent-exit mechanism is **PROVEN** to be the missing frozen-script `__main__` guard; the corrected v0.1.4 release passed exact published-artifact acceptance on the available hosted Windows environment. Phase 3 adds provider/content playback context and structured VLC transport/error telemetry, while populated real-provider compatibility, MAG watchdog behavior, and consumer-endpoint playback remain **NOT TESTED** or **REQUIRES AUTHORIZED PROVIDER VALIDATION**. See [WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md](WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md), [docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md), and the [Phase 3 implementation audit](IPTVNATOR_INFORMED_PLAYBACK_RELIABILITY_IMPLEMENTATION_AUDIT.md).

Development follows the repository’s direct-to-`main` quality sequence:

```text
Inspect → Implement → Test → Quality gate → Commit → Push → Verify remote
```

## Support SamoTech

If SamoTech IPTV Player is useful to you, you can support continued development through [GitHub Sponsors](https://github.com/sponsors/SamoTech). The repository’s funding configuration points to the same `SamoTech` Sponsors profile.

## Attribution

SamoTech IPTV Player thanks **KiddaC** for the engineering work behind [EStalker](https://github.com/kiddac/EStalker) and [XStreamity](https://github.com/kiddac/XStreamity). These public repositories were studied as technical references for practical IPTV patterns, including Xtream/Stalker workflows, catalogue handling, Series/Season/Episode navigation, provider behavior, playback resolution, and related engineering concerns.

SamoTech IPTV Player is an independent project and is **not a clone of EStalker or XStreamity**. Their Enigma2-specific architecture, UI, global-state model, service/decoder APIs, and legacy persistence model were not adopted as SamoTech architecture. In particular, Enigma2 service/player values such as `1`, `4097`, `5001`, `5002`, and `8193` are **not generic IPTV or VLC protocols**; they select Enigma2 playback backends and must not be copied into the Windows/libVLC player. No external source code was copied into this implementation, and no partnership, endorsement, ownership, or code-reuse claim is made. Readers should respect the original projects and any license or attribution terms they publish.

## License

MIT — see [LICENSE](LICENSE).

[1]: https://github.com/SamoTech/samotech-iptv-player "SamoTech IPTV Player repository"
[2]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.1 "SamoTech IPTV Player v0.1.1 release"
[3]: https://github.com/SamoTech/samotech-iptv-player/actions/workflows/windows-release-artifact-acceptance.yml "Exact-release Windows acceptance workflow"
[4]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32143064567 "Exact published v0.1.4 Windows acceptance run"
[5]: https://github.com/SamoTech/samotech-iptv-player/blob/main/SECURITY_CODEQL_LOGGING_REMEDIATION_AUDIT.md "Security and CodeQL remediation audit"
[6]: https://github.com/SamoTech/samotech-iptv-player/blob/main/WINDOWS_SILENT_EXIT_FORENSIC_AUDIT.md "Authoritative Windows silent-exit forensic audit"
