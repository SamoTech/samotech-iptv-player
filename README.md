# SamoTech IPTV Player

> **An extensible, provider-agnostic IPTV desktop player and media-platform foundation.**

SamoTech IPTV Player is a Python project for connecting authorized IPTV sources through provider-specific adapters, translating their records into a canonical domain model, resolving eligible media streams, and presenting the supported workflow in a PySide6/Qt desktop shell backed exclusively by libVLC. It is designed to grow across provider ecosystems without coupling the application domain, use cases, or desktop UI to a provider protocol.

The repository currently contains substantial, tested foundations for M3U, Xtream Codes, and MAG/Stalker live-TV workflows, SQLite-backed non-secret user state, OS-keyring credential ownership, a Qt/libVLC presentation shell, recording controls, and persisted theme settings. It is **not yet a packaged, one-command end-user application**: the next milestone is the production composition and lifecycle that connects the existing components into a runnable desktop application.

For the authoritative current-state matrices, known limitations, verification baseline, and next milestone, read [PROJECT_STATUS.md](PROJECT_STATUS.md). The delivery sequence is maintained in [ROADMAP.md](ROADMAP.md).

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

## Product purpose

The project provides an architecture for a desktop IPTV experience that can connect to multiple authorized content sources while preserving a stable internal model for channels, categories, streams, movies, series, episodes, programme guide entries, favorites, history, and settings. Each provider adapter owns its provider protocol, credential interpretation, and volatile session behavior. The rest of the application works with canonical domain records and application ports rather than raw provider payloads.

> **Important distinction:** a provider ecosystem, a playlist or manifest format, a stream transport, and a player backend are separate concepts. M3U, Xtream Codes, and MAG/Stalker are source/provider concerns; M3U/M3U8, HLS, and MPD are playlist or manifest concerns; HTTP(S), RTMP(S), RTSP, UDP, RTP, and SRT are transport classifications; and libVLC is the sole supported decoding and playback backend.

## What the project can do today

The current codebase implements tested boundaries for the following capabilities. “Implemented” means executable through the stated layer and covered by focused tests; it does not imply that all capabilities have already been wired into a packaged end-user launcher.

| Area | Current capability |
|---|---|
| Provider registration | Credential-safe manual registration flows for M3U, Xtream Codes, and MAG/Stalker profiles. |
| Provider isolation | Provider adapters translate protocol data to canonical domain records and keep credentials/session state in infrastructure. |
| Live-TV workflow | Registered-provider browsing, channel search, provider-specific live stream resolution where supported, libVLC playback orchestration, and Qt native video-surface attachment. |
| Library state | SQLite persistence foundations for provider metadata, favorites, history, and non-secret theme preferences. |
| Programme guide | Provider EPG grid for MAG/Stalker and Xtream short EPG; bounded secure XMLTV parsing with explicit source-channel mappings. |
| Player controls | libVLC play, pause, resume, stop, native video output, and local MPEG transport-stream recording. |
| Desktop shell | PySide6 dialogs for provider entry, provider listing, channel browsing, EPG display, recording actions, and theme settings; qasync runtime support. |
| Theme settings | Persisted system/light/dark preference, deterministic Qt stylesheet application, startup initial-theme support, and a Settings menu/dialog. |
| Extensibility | Explicitly selected trusted local Python provider-plugin SDK with API-version and namespace validation. |

## Supported providers and content sources

| Provider or source | Status | What is available now | What remains |
|---|---|---|---|
| M3U | **Partially Implemented** | Local/file/HTTP(S) source loading, extended-M3U parsing, secure tokenized-source handling, canonical live channels, and local search. | No canonical M3U playback-provider implementation in the registered-player path; no VOD/series UI or XMLTV source binding. |
| Xtream Codes API | **Partially Implemented** | Credential validation, live channels, live/VOD/series categories, movies, series, short EPG, local channel search, and live stream URL resolution. | VOD/series/category capability exposure through registered-provider use cases and desktop catalogue UI; broader playback/track UX. |
| MAG/Stalker | **Partially Implemented** | Authorized MAC identity handling, session refresh, live channels, EPG, local channel search, and live stream resolution. | Canonical VOD, series, category-family, catch-up/archive, and user-facing catalogue workflows. |
| Ministra | **Planned** | Compatibility assessment and a separate-adapter design decision. | Authorized sanitized fixture, approved device identity, dedicated device-facing adapter, handshake/profile/catalogue/link-resolution implementation. |
| Trusted local provider plugins | **Implemented** | Explicit local-file loading, API version/identity/namespace validation, transactional registration, and a tested reference plugin. | Sandbox, signing, marketplace, automatic discovery, remote installation, and plugin updating are deliberately out of scope. |

## Playlist, manifest, and stream-protocol status

| Technology | Status | Current behavior |
|---|---|---|
| Extended M3U | **Implemented** | Parses channel metadata and stream URIs into canonical `Channel` and `Stream` records. |
| M3U8/HLS manifest | **Partially Implemented** | Bounded parser handles HLS master/media manifest metadata; adaptive playback logic is delegated to libVLC rather than implemented in Python. |
| MPEG-DASH MPD | **Partially Implemented** | Bounded safe parser reads MPD live/VOD type and representation metadata; no adaptive playback logic exists in the application. |
| XMLTV | **Partially Implemented** | Bounded `defusedxml` parser creates canonical EPG records for explicit source-channel mappings; source discovery/fetching and binding are not composed. |
| HTTP and HTTPS | **Partially Implemented** | Canonical stream-URI validation/classification; actual playback relies on libVLC and provider-resolved URLs. |
| RTMP, RTMPS, RTSP, UDP, RTP, SRT | **Partially Implemented** | Canonical URI validation/classification exists; no application-level transport capability negotiation or dedicated user experience exists. |

## Supported content and desktop features

| Capability | Status | Current scope |
|---|---|---|
| Live TV | **Partially Implemented** | M3U, Xtream, and MAG adapters can model live channels; Xtream and MAG expose live stream resolution through the registered-provider path. |
| Movies/VOD | **Partially Implemented** | Canonical domain records and Xtream provider catalogue methods exist. No registered-provider movie browsing/playback UI is present. |
| Series and episodes | **Partially Implemented** | Canonical domain records and Xtream series catalogue methods exist. No series/episode browse/playback workflow is present. |
| EPG | **Partially Implemented** | MAG/Stalker and Xtream adapter EPG plus a safe Qt grid are implemented. XMLTV integration and catch-up/archive behavior are not wired. |
| Catch-up/archive | **Planned** | Capability vocabulary exists, but no executable provider or UI workflow exists. |
| Favorites | **Partially Implemented** | SQLite persistence and adding a selected channel from the browser are implemented. Listing/removal UI is absent. |
| History | **Partially Implemented** | SQLite persistence and playback-time recording use case are implemented. History UI and resume workflow are absent. |
| Provider management | **Partially Implemented** | Add and list flows are implemented. Restore/lifecycle composition, edit/remove UI, and operational diagnostics are absent. |
| Search | **Implemented** | Provider-scoped live-channel search is available through M3U, Xtream, and MAG adapters and the channel browser. |
| Recording | **Implemented** | libVLC duplicate-output recording to a timestamped local `.ts` file with generic UI feedback. |
| Settings and theme | **Implemented** | Persisted system/light/dark preference, application stylesheets, and Settings dialog. |

## Architecture overview

The architecture keeps dependencies pointed inward and keeps provider protocols separate from desktop UI and player code.

```text
Authorized IPTV provider or source
        ↓
Provider adapter and protocol DTOs
        ↓
Infrastructure translator
        ↓
Canonical domain entities and value objects
        ↓
Application use cases and ports
        ↓
Authorized stream resolution
        ↓
PlayerPort → libVLC
        ↓
PySide6/Qt desktop UI
```

The `domain` package contains framework-independent business records and validation. The `application` package orchestrates use cases through abstract ports. The `infrastructure` package owns provider clients, parsing, SQLite persistence, OS keyring storage, and the libVLC adapter. The `presentation` package owns PySide6 views, dialogs, the native video surface, and theme styling. The architecture is described in detail in [ARCHITECTURE.md](ARCHITECTURE.md).

## Current implementation status and limitation

The principal product gap is not a missing theme or a lack of abstract provider APIs. It is the absence of a production composition root and application entry point that initializes repositories, restores safe provider metadata, constructs provider services and use cases, loads the theme, starts the desktop runtime, and shuts resources down predictably. Consequently, the repository offers tested application components but does not yet provide a complete, supported command for a user to launch and operate the player end-to-end.

The detailed prioritization is maintained in [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md).

## Installation

The project requires **Python 3.12 or newer**. Runtime dependencies include `aiohttp`, `defusedxml`, `keyring`, `python-vlc`, `PySide6`, and `qasync`.

```bash
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
python -m venv .venv
. .venv/bin/activate             # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

A normal library installation is supported with:

```bash
pip install .
```

On a real desktop system, libVLC itself must also be available to the operating system; `python-vlc` is a Python binding, not a bundled VLC runtime.

## Development setup and testing

Run the project’s quality gate before every commit:

```bash
black --check src tests
ruff check src tests
mypy src
pytest -q
git diff --check
```

The GitHub CI workflow also verifies the project on Python 3.13 and runs a best-effort Windows PyInstaller build. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Running the application

A supported production launcher is **not yet available**. The repository currently supplies the tested `build_desktop_application()` composition factory and `run_desktop_application()` qasync runtime boundary, but no executable production composition root invokes them. The next roadmap milestone addresses this gap before packaging, auto-updating, or telemetry work.

## Project structure

```text
src/samotech_iptv/
├── domain/          Canonical IPTV records, value objects, and repository interfaces
├── application/     Use cases, DTOs, and abstract provider/player/storage ports
├── infrastructure/  Provider adapters, parsers, SQLite, keyring, networking, libVLC, plugins
├── presentation/    PySide6 dialogs, views, widgets, theme engine
├── desktop_bootstrap.py
└── desktop_runtime.py

providers/           Legacy MAG provider implementation used behind the MAG adapter
plugins/             Reference trusted local provider plugin
```

## Security model

Provider credentials, MAC addresses, session tokens, and resolved playback URLs can be sensitive. The project keeps credentials in the OS keyring; persists only non-secret provider metadata in SQLite; keeps tokens/session state inside runtime adapters; and directs Qt dialogs to display only credential-safe summaries and generic failure messages. Tokenized M3U sources are treated as secrets and are not stored in provider metadata.

Do not commit credentials, tokens, personal portal URLs, authorized MAC addresses, or captured provider payloads. Tests must use fake values. See [SECURITY.md](SECURITY.md), [docs/m3u_secure_source_design.md](docs/m3u_secure_source_design.md), and [docs/PLUGIN_SDK.md](docs/PLUGIN_SDK.md).

## Roadmap and contribution model

[ROADMAP.md](ROADMAP.md) maps completed work to product milestones and defines the next delivery sequence. Development uses a permanent direct-to-`main` workflow:

```text
Inspect → Implement → Test → Quality gate → Commit → Push main → Verify remote → Continue
```

No feature branches or pull requests are used unless explicitly requested. Every change must pass the quality gate and must not include secrets or knowingly broken code. Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
