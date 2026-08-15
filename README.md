# SamoTech IPTV Player

> **An extensible, provider-agnostic IPTV desktop player and media-platform foundation.**

SamoTech IPTV Player is a Python project for connecting authorized IPTV sources through provider-specific adapters, translating their records into a canonical domain model, resolving eligible media streams, and presenting the supported workflow in a PySide6/Qt desktop shell backed exclusively by libVLC. It is designed to grow across provider ecosystems without coupling the application domain, use cases, or desktop UI to a provider protocol.

The repository currently contains substantial, tested foundations for M3U, Xtream Codes, and MAG/Stalker live-TV workflows, SQLite-backed non-secret user state, OS-keyring credential ownership, a Qt/libVLC presentation shell, recording controls, persisted theme settings, and a production lifecycle that safely wires, starts, and closes those components. It exposes a supported source-install entry point, although release packaging, installers, updates, and production diagnostics remain future work.

For the authoritative current-state matrices, known limitations, verification baseline, and next milestone, read [PROJECT_STATUS.md](PROJECT_STATUS.md). The delivery sequence is maintained in [ROADMAP.md](ROADMAP.md).

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

## Product purpose

The project provides an architecture for a desktop IPTV experience that can connect to multiple authorized content sources while preserving a stable internal model for channels, categories, streams, movies, series, episodes, programme guide entries, favorites, history, and settings. Each provider adapter owns its provider protocol, credential interpretation, and volatile session behavior. The rest of the application works with canonical domain records and application ports rather than raw provider payloads.

> **Important distinction:** a provider ecosystem, a playlist or manifest format, a stream transport, and a player backend are separate concepts. M3U, Xtream Codes, and MAG/Stalker are source/provider concerns; M3U/M3U8, HLS, and MPD are playlist or manifest concerns; HTTP(S), RTMP(S), RTSP, UDP, RTP, and SRT are transport classifications; and libVLC is the sole supported decoding and playback backend.

## What the project can do today

The current codebase implements tested boundaries for the following capabilities. “Implemented” means executable through the stated layer and covered by focused tests; it does not imply that an end-user launcher, packaging, or complete operational lifecycle already exists.

| Area | Current capability |
|---|---|
| Provider registration | Credential-safe manual registration flows for M3U, Xtream Codes, and MAG/Stalker profiles. |
| Provider isolation | Provider adapters translate protocol data to canonical domain records and keep credentials/session state in infrastructure. |
| Live-TV workflow | Registered-provider browsing, channel search, provider-specific live stream resolution where supported, libVLC playback orchestration, and Qt native video-surface attachment. |
| Library state | SQLite-backed Favorites and History libraries with safe listing, refresh, Favorite single-record removal, History clear-all confirmation, duration, recency, and persisted playback-position display. |
| Programme guide | Provider EPG grid for MAG/Stalker and Xtream short EPG; bounded secure XMLTV parsing; registered-provider local/file XMLTV binding with explicit source-channel mappings and manual safe refresh. |
| Player controls | libVLC play, pause, resume, stop, native video output, and local MPEG transport-stream recording. |
| Desktop shell | PySide6 dialogs for provider entry, provider listing/management, Live browsing, capability-driven browse-only Movie/Series catalogues, registered live-category discovery, EPG display, recording actions, and theme settings; qasync runtime support; production composition of safe state, provider services, use cases, theme, and one libVLC player. |
| Non-live contract foundation | Provider-neutral Movie/Episode resolution and Series-detail discovery contracts, safe Season/Episode projections, capability-aware provider resolution, and fake-backed discovery generation tests. No concrete provider declares or executes these new contracts yet. |
| Theme settings | Persisted system/light/dark preference, deterministic Qt stylesheet application, startup initial-theme support, and a Settings menu/dialog. |
| Extensibility | Explicitly selected trusted local Python provider-plugin SDK with API-version and namespace validation. |

## Supported providers and content sources

| Provider or source | Status | What is available now | What remains |
|---|---|---|---|
| M3U | **Partially Implemented** | Local/file/HTTP(S) source loading, extended-M3U parsing, secure tokenized-source handling, canonical live channels/search, and parsed HTTP(S) stream resolution through the registered-player path. | Non-HTTP(S) transports remain classified but are outside the current `URL`/player boundary; no VOD/series UI. XMLTV binding is registered-provider scoped and local/file only. |
| Xtream Codes API | **Partially Implemented** | Credential validation, live channels, registered **live-category** discovery, live/VOD/series category adapter methods, browse-only Movie/Series catalogues, short EPG, local channel search, and live stream URL resolution. | No Movie resolver, Series-detail/season resolver, Episode discovery resolver, or Episode resolver is implemented or advertised; non-live playback remains unavailable. |
| MAG/Stalker | **Partially Implemented** | Authorized MAC identity handling, bounded six-candidate handshake discovery, failure-safe owned HTTP-session cleanup, explicit session lifecycle, legacy, Stalker-query, GUI, and helper request profiles, optional explicit MAG model identity, live channels, EPG, local channel search, and live stream resolution. A source-derived local middleware laboratory now exercises the full adapter boundary. | Production portal compatibility remains provider-specific and unresolved: no authorized candidate returned a structurally valid token-bearing handshake. Official login/password, authorization-key, new-STB, and model-policy modes are documented as provider-side possibilities but are not silently selected. Windows/libVLC availability is separately observed, but MAG remains blocked before stream resolution. Canonical VOD, series, category-family, catch-up/archive, and user-facing catalogue workflows remain open. |
| Ministra | **Compatibility Investigation** | Official Infomir configuration research, open-source Stalker/Ministra source inspection, and a deterministic local source-derived lab are documented. | The authorized portal's middleware family, version, routing, and STB authorization policy remain unidentified; no dedicated Ministra production adapter is claimed. |
| Trusted local provider plugins | **Implemented** | Explicit local-file loading, API version/identity/namespace validation, transactional registration, and a tested reference plugin. | Sandbox, signing, marketplace, automatic discovery, remote installation, and plugin updating are deliberately out of scope. |

## Playlist, manifest, and stream-protocol status

| Technology | Status | Current behavior |
|---|---|---|
| Extended M3U | **Implemented** | Parses channel metadata and stream URIs into canonical `Channel` and `Stream` records, then resolves parsed HTTP(S) streams through the registered-player path. |
| M3U8/HLS manifest | **Partially Implemented** | Bounded parser handles HLS master/media manifest metadata; adaptive playback logic is delegated to libVLC rather than implemented in Python. |
| MPEG-DASH MPD | **Partially Implemented** | Bounded safe parser reads MPD live/VOD type and representation metadata; no adaptive playback logic exists in the application. |
| XMLTV | **Partially Implemented** | Bounded `defusedxml` parser creates canonical EPG records for explicit source-channel mappings. Registered providers can persist a local path or local `file:` source and manually refresh safe title/time rows. | Remote/tokenized source storage or retrieval, source discovery, programme-entry caching/retention, scheduled refresh, catch-up linkage, and playback are not implemented. |
| HTTP and HTTPS | **Partially Implemented** | Canonical stream-URI validation/classification; actual playback relies on libVLC and provider-resolved URLs. |
| RTMP, RTMPS, RTSP, UDP, RTP, SRT | **Partially Implemented** | Canonical URI validation/classification exists; no application-level transport capability negotiation or dedicated user experience exists. |

## Supported content and desktop features

| Capability | Status | Current scope |
|---|---|---|
| Live TV | **Partially Implemented** | M3U, Xtream, and MAG adapters can model live channels and resolve supported HTTP(S) streams through the registered-provider path. Xtream live categories can be browsed through a separate registered-provider dialog; this path has no content-selection or player operation. |
| Movies/VOD | **Partially Implemented** | Canonical Movie records, Xtream catalogue browsing, a capability-driven browse-only desktop catalogue, and a provider-neutral Movie-resolution contract exist. No provider advertises that resolver and no Movie playback UI/path exists. |
| Series and episodes | **Partially Implemented** | Canonical Series and provider-scoped Season records, safe provider-scoped Episode discovery DTOs, Xtream Series catalogue browsing, a browse-only desktop Series catalogue, and provider-neutral Series-detail/Episode-resolution contracts exist. No provider advertises Series detail, Episode discovery, or Episode playback; no season/episode UI exists. |
| EPG | **Partially Implemented** | MAG/Stalker and Xtream adapter EPG plus a safe Qt grid are implemented. A separate Qt dialog configures local/file XMLTV mappings and manually displays bounded title/time entries. | Remote/tokenized XMLTV delivery, persisted guide cache, scheduled refresh, and catch-up/archive behavior are not wired. |
| Catch-up/archive | **Planned** | Capability vocabulary exists, but no executable provider or UI workflow exists. |
| Favorites | **Implemented** | SQLite persistence, browser insertion, library listing, empty state, refresh, generic errors, and single-record removal are implemented. |
| History | **Implemented** | SQLite persistence, recent library listing, duration, recency, persisted playback-position display, refresh, generic errors, and confirmation-protected clear-all are implemented. Per-record deletion, replay, and resume are not implemented. |
| Provider management | **Implemented for registered profiles** | Add/list/edit/remove flows, safe metadata restoration, blank-credential preservation, and keyring cleanup on removal are implemented. Confirmation UX and operational diagnostics remain limited. |
| Search | **Implemented** | Provider-scoped live-channel search is available through M3U, Xtream, and MAG adapters and the channel browser. |
| Recording | **Implemented** | libVLC duplicate-output recording to a timestamped local `.ts` file with generic UI feedback. |
| Settings and theme | **Implemented** | Persisted system/light/dark preference, application stylesheets, and Settings dialog. |

## Architecture overview

The architecture keeps dependencies pointed inward and keeps provider protocols separate from desktop UI and player code. MAG protocol construction remains in the legacy provider/profile layer; the MAG adapter owns application translation and session lifecycle.

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

The dependency-wiring, launch-lifecycle, primary registered live-stream, provider-management, XMLTV, and user-library foundations are now delivered: `build_production_desktop_application()` initializes safe SQLite state, restores provider metadata, constructs provider services and use cases, loads the persisted theme, and shares one libVLC player with the Qt shell; `samotech-iptv` and `python -m samotech_iptv` invoke that graph, run qasync, report startup failure generically, and close the shared HTTP resource; M3U, Xtream, and MAG resolve supported HTTP(S) live streams through the registered-provider path. Favorites and History are now user-testable at their bounded library-view scope; replay/resume and non-live catalogue workflows remain future work.

The detailed prioritization is maintained in [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md). MAG protocol scope and compatibility evidence are documented in [docs/MAG_PROTOCOL.md](docs/MAG_PROTOCOL.md), [docs/MAG_FIRMWARE_COMPATIBILITY.md](docs/MAG_FIRMWARE_COMPATIBILITY.md), and [docs/MAG_TEST_LAB.md](docs/MAG_TEST_LAB.md).

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

The GitHub CI workflow also verifies the project on Python 3.13 and runs a best-effort Windows PyInstaller build. The deterministic MAG protocol lab is included in the pytest suite; it is a local protocol simulation and does not claim production portal compatibility. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Running the application

After installing from source, run the desktop application with either supported entry point:

```bash
samotech-iptv
# equivalent:
python -m samotech_iptv
```

The entry point composes safe local state, restores registered provider metadata, loads the theme, starts the qasync runtime, and closes the shared HTTP resource when the window loop exits. Startup failures are reported generically so exception details do not expose provider information. A standalone installer, auto-updater, crash-reporting policy, and release distribution remain future work.

### Windows development and safe MAG transport diagnostics

For a detailed, timed provider-operation trace in PowerShell, enable the existing debug configuration before launching:

```powershell
$env:IPTV_DEBUG="1"
samotech-iptv
```

With debug enabled, the console shows provider operation stages, elapsed timing, HTTP status and response-size metadata, parser/translation summaries, safe optional-field warnings, and redacted full tracebacks. Credentials, tokens, cookies, authorization headers, and credential-bearing URLs are not logged. To return to normal concise behavior, use:

```powershell
$env:IPTV_DEBUG="0"
samotech-iptv
```

For an authorized MAG catalogue measurement, `INFO` logging is sufficient to emit three aggregate-only transport records: `CATALOGUE_HTTP_RESPONSE` after response headers, `CATALOGUE_BODY_COMPLETE` after the full body, and `CATALOGUE_BODY_INCOMPLETE` when collection fails. They include only attempt/timeout metadata, HTTP metadata, aggregate byte and chunk counts, body timing, and a `TIMEOUT`, `PAYLOAD_ERROR`, or `NETWORK_ERROR` classification. They never include portal URLs, MAC identities, tokens, cookies, authorization headers, credentials, response bodies, or stream URLs.

```powershell
$env:IPTV_LOG_LEVEL="INFO"
python -m samotech_iptv
```

Perform one normal catalogue load in the application, then collect only those `CATALOGUE_*` records together with the existing safe catalogue shape/parse and `MAG LOAD_CHANNELS` lines. Reset the process-local diagnostic level or close the PowerShell window when finished. The records establish response-boundary facts only; do not infer a provider or qasync root cause from a single run.

## Project structure

```text
src/samotech_iptv/
├── domain/          Canonical IPTV records, value objects, and repository interfaces
├── application/     Use cases, DTOs, and abstract provider/player/storage ports
├── infrastructure/  Provider adapters, parsers, SQLite, keyring, networking, libVLC, plugins
├── presentation/    PySide6 dialogs, views, widgets, theme engine
├── desktop_bootstrap.py
├── desktop_composition.py
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


## MAG/Stalker compatibility status

The MAG provider includes separate `stalker_gui_compatibility` and `stalker_helper_compatibility` profiles derived from secondary client references. They are **IMPLEMENTED and SIMULATED** through deterministic fixture coverage, with strict token validation, private cookie mapping, live genre/ordered-list handling, helper page-one pagination, command-based stream-link construction, and an optional explicit model field. Without an explicit model, the runtime reports MODEL UNKNOWN and does not fabricate a MAG250/MAG254 identity. The new source-derived middleware laboratory validates the full adapter boundary against local test data. These results are **NOT VERIFIED** against the authorized production portal: no candidate produced a real JSON session token, so MAG channels, stream resolution, and playback must not be inferred from local tests.
