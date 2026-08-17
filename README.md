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
| Player controls | libVLC play, pause, resume, stop, native video output, local MPEG transport-stream recording, and bounded Live EOF recovery. Recovery is locally deterministic-test validated, but Windows-native and authorized-provider runtime confirmation remain pending. |
| Desktop shell | PySide6 dialogs for provider entry, provider listing/management, Live browsing, capability-driven browse-only Movie/Series catalogues, registered live-category discovery, EPG display, recording actions, and theme settings; qasync runtime support; production composition of safe state, provider services, use cases, theme, and one libVLC player. |
| Non-live workflow | Xtream Movie detail/playback, Series → Season → Episode discovery/playback, provider-scoped canonical identities, generation-safe stale-result protection, local catalogue category/search/sort controls, and shared `ResolvedPlayback`/`PlayerPort` handoff. |
| Theme settings | Persisted system/light/dark preference, deterministic Qt stylesheet application, startup initial-theme support, and a Settings menu/dialog. |
| Extensibility | Explicitly selected trusted local Python provider-plugin SDK with API-version and namespace validation. |

## Supported providers and content sources

| Provider or source | Status | What is available now | What remains |
|---|---|---|---|
| M3U | **Partially Implemented** | Local/file/HTTP(S) source loading, extended-M3U parsing, secure tokenized-source handling, canonical live channels/search, and parsed HTTP(S) stream resolution through the registered-player path. | Non-HTTP(S) transports remain classified but are outside the current `URL`/player boundary; no VOD/series UI. XMLTV binding is registered-provider scoped and local/file only. |
| Xtream Codes API | **Partially Implemented** | Credential validation, normalized account/server metadata, live channels/categories, VOD/Series categories, Movie details/playback, Series → Season → Episode discovery/playback, short EPG, local search, and local category/search/sort controls. | Authorized populated real VOD/Series runtime evidence remains pending; richer enrichment, broader provider quirks, and executable catch-up remain future work. |
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
| Movies/VOD | **Partially Implemented** | Canonical Movie records, Xtream catalogue/detail loading, local category/search/sort controls, explicit Movie detail/play activation, opaque provider-scoped playback resources, and shared-player resolution. |
| Series and episodes | **Partially Implemented** | Canonical Series/Season/Episode records, Xtream Series → Season → Episode navigation, local category/search/sort controls, generation-safe detail/discovery, and Episode playback through the shared player path. |
| EPG | **Partially Implemented** | MAG/Stalker and Xtream adapter EPG plus a safe Qt grid are implemented. A separate Qt dialog configures local/file XMLTV mappings and manually displays bounded title/time entries. | Remote/tokenized XMLTV delivery, persisted guide cache, scheduled refresh, and catch-up/archive behavior are not wired. |
| Catch-up/archive | **Planned** | Capability vocabulary exists, but no executable provider or UI workflow exists. |
| Favorites | **Implemented** | SQLite persistence, browser insertion, library listing, empty state, refresh, generic errors, and single-record removal are implemented. |
| History | **Implemented / Bounded** | SQLite persistence, provider-scoped identity, recent library listing, duration, recency, persisted playback-position display, throttled non-live progress, completion, incomplete Movie/Episode resume restoration, refresh, generic errors, and confirmation-protected clear-all are implemented. Per-record deletion and direct replay/navigation remain outside the current contract. |
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

The dependency-wiring, launch-lifecycle, registered live-stream, provider-management, XMLTV, user-library, and Xtream non-live foundations are now delivered: `build_production_desktop_application()` initializes safe SQLite state, restores provider metadata, constructs provider services and use cases, loads the persisted theme, and shares one libVLC player with the Qt shell; `samotech-iptv` and `python -m samotech_iptv` invoke that graph, run qasync, report startup failure generically, and close the shared HTTP resource. M3U, Xtream, and MAG resolve supported HTTP(S) live streams through the registered-provider path, while Xtream Movie and Episode targets resolve through the same provider-neutral playback path and Series navigation remains container-only. The player also contains bounded, Live-only EOF recovery with deterministic local coverage; it is a mitigation rather than a root-cause claim, and native Windows/authorized-provider runtime confirmation remains pending. Favorites and History are user-testable at their bounded library-view scope; per-record history deletion/direct replay and populated authorized real-Xtream runtime evidence remain pending.

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

The GitHub CI workflow also verifies the project on Python 3.13. Its Windows job installs standard VLC, runs a provider-free native libVLC lifecycle probe, and runs the deterministic Live EOF recovery suite as blocking gates; only the later PyInstaller artifact step is best-effort. The Windows job has executed successfully, but that CI evidence does not replace the separate authorized Windows Live IPTV runtime procedure. The deterministic MAG protocol lab is included in the pytest suite; it is a local protocol simulation and does not claim production portal compatibility. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

The Ubuntu quality job intentionally runs the real offscreen PySide6 player-shell probes. It installs only the runner-native `libegl1` package required to provide `libEGL.so.1`, verifies `PySide6.QtGui` and `PySide6.QtWidgets` imports with `QT_QPA_PLATFORM=offscreen`, then executes both standalone probes before the coverage suite. This is CI-environment provisioning rather than an application dependency or a test skip.

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

## Acknowledgements

SamoTech IPTV Player would like to thank **KiddaC** for the engineering work behind [EStalker](https://github.com/kiddac/EStalker) and [XStreamity](https://github.com/kiddac/XStreamity).

These publicly available projects were studied as technical and engineering references to better understand practical IPTV technologies and patterns, including Xtream/Stalker workflows, catalogue handling, Series/Season/Episode navigation, provider behavior, playback resolution, and related engineering concerns. SamoTech is an independent project and is **not a clone of EStalker or XStreamity**. Their Enigma2-specific application architecture, UI, global state model, service/decoder APIs, and legacy persistence model were not adopted as SamoTech architecture.

The relevant concepts were evaluated and adapted only where they fit SamoTech’s own Python, domain/application, PySide6, qasync, and libVLC architecture. No external source code from EStalker or XStreamity was copied into the implementation. The repositories did not expose an SPDX license in the inspected GitHub metadata or a tracked root license file; this acknowledgment makes no claim of permission, endorsement, partnership, ownership, or code-reuse rights. Readers should respect the original projects and any license or attribution terms they publish.

## License

MIT — see [LICENSE](LICENSE).


## MAG/Stalker compatibility status

The MAG provider includes separate `stalker_gui_compatibility` and `stalker_helper_compatibility` profiles derived from secondary client references. They are **IMPLEMENTED and SIMULATED** through deterministic fixture coverage, with strict token validation, private cookie mapping, live genre/ordered-list handling, helper page-one pagination, command-based stream-link construction, and an optional explicit model field. Without an explicit model, the runtime reports MODEL UNKNOWN and does not fabricate a MAG250/MAG254 identity. The new source-derived middleware laboratory validates the full adapter boundary against local test data. These results are **NOT VERIFIED** against the authorized production portal: no candidate produced a real JSON session token, so MAG channels, stream resolution, and playback must not be inferred from local tests.

## Commercial Xtream VOD/Series increment — 2026-08-16

The Xtream VOD and Series catalogue now carries optional provider-supplied Movie metadata such as duration, genre, director, cast, country, release date, format, poster, and backdrop, plus Series genre, artwork, and available season/episode counts. The existing PySide6 catalogue renders this information in an inline, keyboard-friendly detail panel with safe fallback text; it does not fetch artwork, construct playback URLs, or add an uncontrolled cache. Missing or malformed optional values are ignored while required identity remains strict.

Xtream search, category filtering, and opt-in local sorting remain no-network operations over the explicitly loaded catalogue. Provider order remains the default. Movie and Episode playback continue through the existing `PlaybackTarget` → `ResolvedPlayback` → `PlayerPort` → libVLC path, while Series containers remain non-playable. Populated authorized real-provider validation, resume reconstruction, catch-up, audio/subtitle tracks, and remote artwork loading remain explicitly partial or deferred.


## Advanced Xtream VOD/Series increment — 2026-08-16

The advanced increment preserves the existing provider adapters, canonical DTOs, qasync task ownership, stale-result protection, typed playback ports, shared HTTP session, SQLite user state, and libVLC backend. It adds provider-supplied Movie/Series detail metadata to local search, category filtering, sorting, and the inline detail panel; a bounded provider-scoped artwork loader that reuses the shared HTTP client; safe artwork URL validation and size limits; native placeholder/decode/error states; Movie and Series Favorite actions; and provider-scoped Favorite persistence with legacy SQLite migration and duplicate prevention.

The classification remains evidence-based. **Movie and Series details, local metadata search, category/filter, sort, artwork loading, provider switching, Favorite persistence, and stale UI protection are implemented and synthetically/native tested.** Episode Favorites remain unavailable because the existing Favorite domain contract supports only channel, movie, and series. Watched badges, true resume, progress updates, catch-up, track selection, external metadata enrichment, and populated-provider acceptance remain **deferred, provider-dependent, or blocked by existing typed contracts/evidence**. The authorized provider session used in the prior increment returned zero VOD/Series records, so no populated-provider behavior is claimed here.

See [`ADVANCED_XTREAM_VOD_SERIES_FINAL_AUDIT.md`](ADVANCED_XTREAM_VOD_SERIES_FINAL_AUDIT.md) for the ordered Todo List, implementation evidence, quality gates, security review, and remaining actions.


## Real Xtream acceptance and production-hardening status — 2026-08-16

The source-level and synthetic/native Xtream VOD/Series implementation remains ready. A subsequent controlled acceptance phase reviewed the standard Xtream action surface, response-shape tolerance, bounded artwork, provider-scoped Favorites, History/resume limits, PlayerPort capabilities, commercial native UX, concurrency, security, and exact 10K/50K/100K performance checkpoints.

Populated real-provider acceptance remains **BLOCKED BY EVIDENCE**: no authorized populated account was available in the current environment, and the previously authorized session returned zero VOD and Series records. Windows native acceptance is **NOT EXECUTED** on Linux; the Windows-only VLC probe explicitly reports `SKIP reason=windows_required`. These states are not converted into PASS claims.

See [`XTREAM_REAL_ACCEPTANCE_AND_PRODUCTION_HARDENING_FINAL_AUDIT.md`](XTREAM_REAL_ACCEPTANCE_AND_PRODUCTION_HARDENING_FINAL_AUDIT.md) for the 32-section final audit, compatibility matrix, acceptance matrix, PlayerPort capability classification, security review, and remaining actions.

## Player 2 commercial playback increment — 2026-08-16

Player 2 now provides a typed playback capability model and explicit state machine over the preserved `PlaybackTarget` → `ResolvedPlayback` → `PlayerPort` → libVLC path. The commercial overlay includes mode-aware elapsed/duration and seek controls for Movie and Episode, Live-safe control suppression, relative seeks, volume, mute, native audio/subtitle menus, aspect ratio, restart, diagnostics, true fullscreen, keyboard shortcuts, and owned asynchronous work.

History persistence now supports provider-scoped identity, runtime position and duration, watched percentage, timestamps, completion, safe SQLite migration, throttled non-live progress updates, and provider-scoped resume restoration. Live playback is never resumed or marked completed from unknown duration.

Validation is recorded in [`docs/PLAYER_2_RUNTIME_VALIDATION.md`](docs/PLAYER_2_RUNTIME_VALIDATION.md), with architecture details in [`docs/PLAYER_2_ARCHITECTURE.md`](docs/PLAYER_2_ARCHITECTURE.md). The full Linux deterministic suite and source quality gates pass. Windows native VLC execution remains **NOT EXECUTED** on Linux, and populated authorized-provider acceptance remains **NOT EXECUTED**; neither limitation is represented as a pass claim.


## Player 3 commercial hardening — 2026-08-16

Player 3 hardens the preserved Player 2 architecture rather than replacing it. Xtream catalogue translation now skips malformed and duplicate live, Movie, Series, Season, and Episode records individually while retaining valid records and emitting safe diagnostics. MAG now advertises its implemented live-category capability. EPG application DTOs preserve safe description and category metadata and clamp the rendered entry count. The PlayerShell adds provider-scoped adjacent-episode navigation and typed backend-state labels without importing libVLC, constructing provider URLs, or accessing credentials.

History construction now enforces timestamp ordering, and the application use cases map domain failures through a stable credential-free error taxonomy. Existing provider-scoped Favorites, bounded artwork caching, Live-only EOF recovery, shared VLC ownership, qasync task ownership, generation guards, and the `PlaybackTarget` → `ResolvedPlayback` → `PlayerPort` path remain intact. Catch-up/archive remains **NOT IMPLEMENTED** because no current provider advertises `ProviderCapability.CATCHUP`.

The Player 3 verification record includes focused regression tests, isolated Qt concurrency/lifecycle runs, the 39,753-live/5,000-content performance probe across required 0–100,000 catalogue sizes, the changed-file security scan, and Linux native-probe classification. Windows-native validation is **NOT EXECUTED** in the Linux environment. Authorized populated Xtream acceptance is **NOT EXECUTED**, and MAG VOD/Series/Episodes remain **NOT EXECUTED** because the authorized portal contract is still unproven. See [PLAYER_3_FINAL_AUDIT.md](PLAYER_3_FINAL_AUDIT.md), [docs/PLAYER_3_ARCHITECTURE.md](docs/PLAYER_3_ARCHITECTURE.md), and [docs/PLAYER_3_RUNTIME_VALIDATION.md](docs/PLAYER_3_RUNTIME_VALIDATION.md).

The Player 3 security boundary is explicit: authorized credentials are entered only through an approved local mechanism and are never stored in source, tests, reports, shell history, or commits. The final audit reports aggregate counts and classifications only; it does not reproduce provider credentials, tokens, cookies, resolved URLs, or raw payloads.

## Player 3 attribution boundary

The public EStalker and XStreamity repositories remain acknowledged as technical references only. Player 3 preserves SamoTech’s own Python, Clean Architecture, PySide6, qasync, SQLite/keyring, and libVLC implementation. No external source code was copied, and no license, endorsement, partnership, or code-reuse claim is made beyond the repository’s existing acknowledgement.


## Smart Provider Import

The Add IPTV Provider workflow now exposes **Smart Import** beside the preserved **Manual Add** path. Smart Import performs deterministic parsing locally: users can paste Xtream server/credential text or complete URLs, M3U URLs or markers, and MAG/Stalker portal/MAC data. The flow is **Paste → Detect → Review → Validate → Add**, while advanced users retain the original protocol-specific manual dialogs and fields. The validation step checks the normalized required fields; it does not claim a network test for an unsaved profile.

Smart Import normalizes detected fields into the existing Xtream, M3U, and MAG registration request DTOs. Provider adapters remain responsible for protocol behavior, credentials remain inside the existing secure registration path, and no clipboard text is sent to an external API or AI service. The preview masks passwords and MAC identities, asks only for missing required fields, and requires explicit protocol selection when input is genuinely ambiguous. Duplicate provider IDs continue to use the existing deterministic registration semantics rather than creating a second provider architecture.

After a successful manual or Smart Import registration, the existing provider state is refreshed through the PlayerShell selector and any open provider-list dialog without restarting the application. Raw inline M3U content can be detected and previewed, but adding it remains unavailable when no URL or local-file source exists because the existing M3U source boundary deliberately does not persist raw clipboard content. Populated real-provider acceptance remains separate from deterministic parser/UI verification and must not be inferred from it.


## Commercial provider and subtitle hardening — 2026-08-17

The desktop shell now includes a credential-free **Provider Health** snapshot and a non-blocking post-save onboarding path. After a provider is saved, the application tests only the declared provider/application boundaries and adapter authentication state; it does not load a full catalogue, display credentials, or block the Qt event loop. Provider lists render safe capability and health summaries, while unknown, unauthenticated, connected, and error states remain distinct.

The local global search now supports **All, Live, Movies, Series, and Episodes** filters over already-loaded canonical records. Episode title, plot, season, and episode-number fields participate in local matching. The implementation does not add provider requests or bypass the existing provider-scoped catalogue and playback contracts.

The shared PlayerPort/libVLC path now supports local subtitle attachment for validated **SRT, ASS, SSA, and VTT** files, explicit subtitle-slave removal, and bounded subtitle delay controls. Files are inspected locally, never uploaded, persisted, logged, or executed. Subtitle operations are guarded by media/session identity so a stale selection cannot attach a file to another movie, episode, channel, provider, or media generation. The UI exposes these controls only when the injected player advertises the corresponding real capability; libVLC remains the sole backend.

Catch-up/archive is still **not implemented** because no current provider advertises the capability or provides a verified playback contract. Windows-native VLC validation and populated authorized-provider acceptance remain separate, unexecuted gates in this Linux environment. See [COMMERCIAL_SUBTITLE_FINAL_AUDIT.md](COMMERCIAL_SUBTITLE_FINAL_AUDIT.md) for the complete evidence matrix.
