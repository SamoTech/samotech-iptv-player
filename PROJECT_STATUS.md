# Project Status — Authoritative Current State

> **Authority:** This document is the sole source of truth for what the repository currently implements, partially implements, and plans. [README.md](README.md) summarizes this state for users and contributors. [ROADMAP.md](ROADMAP.md) explains historical delivery and future direction. Historical reports and assessments are records of their stated date and commit, not current-state authority.

**Product:** SamoTech IPTV Player
**Package version:** `0.1.0`
**Current baseline:** The `main` revision containing the approved bounded Live EOF recovery and Windows validation increment; use `git rev-parse HEAD` for its immutable revision identifier.
**Current product milestone:** Player 3 commercial hardening — **implemented and deterministically validated within the preserved Player 2 architecture; populated authorized Xtream runtime evidence remains not executed**. Xtream malformed/duplicate catalogue handling, MAG live categories, EPG metadata propagation, adjacent-episode controls, typed backend-state rendering, history timestamp invariants, and credential-free error taxonomy are covered by focused tests. Windows-native validation remains not executed in this Linux environment; the bounded Live EOF recovery remains unchanged.
**Baseline verified:** 2026-08-15 UTC+03:00

## Product purpose

SamoTech IPTV Player is an **extensible, provider-agnostic IPTV desktop player and media-platform foundation**. It is intended to connect authorized IPTV content sources, isolate their provider protocols behind infrastructure adapters, translate source records into a canonical domain, resolve authorized streams through application use cases, and provide a PySide6/Qt desktop playback experience driven solely by libVLC.

The project is deliberately broader than any one provider format. It models channels, streams, categories, movies, series, episodes, EPG entries, favorites, history, provider metadata, and non-secret desktop settings in a provider-independent domain. Provider-specific authentication, MAC/device identity, source URLs, session tokens, HTTP payloads, and temporary links remain infrastructure concerns.

## Architectural model

```text
Authorized IPTV provider or content source
        ↓
Provider adapter and provider protocol DTOs
        ↓
Infrastructure translator
        ↓
Canonical domain entities and value objects
        ↓
Application use cases and abstract ports
        ↓
PlaybackResource → provider resolution → ResolvedPlayback
        ↓
PlayerPort → libVLC (sole supported player backend)
        ↓
PySide6/Qt desktop UI (sole supported desktop toolkit)
```

The architecture distinguishes four concerns that are often conflated:

| Concern | Meaning | Current examples |
|---|---|---|
| Provider/content source | A service or source ecosystem that authenticates, catalogs content, supplies EPG, or resolves links. | M3U source, Xtream Codes API, MAG/Stalker portal, planned Ministra portal. |
| Playlist or manifest format | A document that lists content or describes media renditions. | Extended M3U, M3U8/HLS, MPEG-DASH MPD, XMLTV. |
| Stream transport | The delivery scheme classified for a media stream. | HTTP, HTTPS, RTMP, RTMPS, RTSP, UDP, RTP, SRT. |
| Player backend | The engine that renders and decodes resolved media. | libVLC through `python-vlc` only. |

The domain layer does not depend on Qt, libVLC, SQLite, `aiohttp`, `keyring`, or provider libraries. The application layer depends on domain records and abstract ports. Infrastructure implements those ports. Presentation depends on application use cases and uses Qt only for UI.

### Phase 2 playback contract

The playback boundary now separates the logical `PlaybackResource` identity from ephemeral transport requirements and the final `ResolvedPlayback`. `TransportMetadata` is an explicit typed structure for supported headers, user-agent, referrer, and existing protocol/container hints; it is not persisted and does not contain provider credentials. Provider adapters remain responsible for Xtream URL construction, M3U stream lookup, and MAG session/link resolution. `PlayerPort` and the VLC adapter receive only `ResolvedPlayback`, and the VLC adapter translates supported transport metadata into media options without knowing provider identity. Resolved URLs, headers, cookies, signed links, and provider session state remain ephemeral; only safe logical/provider metadata is persisted. Existing Phase 1 attempt-generation, cancellation, stale-result, and provider-switch protections remain in force. MAG remains live-only for this phase, and no new M3U or MAG capabilities were added.

## Desktop UI/UX modernization status

The desktop presentation modernization is **implemented and deterministically validated** within the existing PySide6 architecture. The shared token system provides cinematic dark/blue application styling; the main shell provides a remembered collapsible sidebar, provider/status context, local search across already-loaded Live/Movie/Series content, and explicit loading, empty, and error states. Movie and Series catalogues use reusable content-card delegates while retaining model-backed selection and activation behavior. The player surface adds a presentation-only overlay with idle visibility, status feedback, stop/play-pause controls, fullscreen, and the supported `Space`/`F` shortcuts.

The work is intentionally presentation-scoped. It preserves the existing application use cases, provider adapters, credential boundaries, `PlayerPort`, shared libVLC instance, qasync runtime, and desktop composition contracts. Local global search does not create new network requests, and the UI does not construct provider URLs or read secrets. Native offscreen Qt probing covers sidebar state, loaded-content search grouping, card-view configuration, overlay status/visibility, keyboard shortcuts, and fullscreen delegation. Full repository verification is recorded in the final modernization report.

## Status vocabulary

| Status | Definition |
|---|---|
| **Implemented** | Executable through the stated layer and covered by focused tests. It may still await the lifecycle milestone before it is reachable from a supported end-user launcher. |
| **Partially Implemented** | A real, tested subset or foundation exists, but an essential workflow, capability, integration, or user-facing exposure remains absent. |
| **Planned** | No executable support claim is made. Research, an enum value, or an abstract interface alone is not implementation. |

## Provider and content-source matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| M3U source | Provider/content source | **Partially Implemented** | Local, `file:`, and HTTP(S) source loading; extended-M3U parsing; protected tokenized source storage; canonical live channels/search; parsed HTTP(S) stream resolution into `ResolvedPlayback`. | Source loader, parser, adapter, registered-playback integration, registration, and transport-contract coverage. | The adapter implements `PlaybackProvider` and resolves parsed HTTP(S) channels through the provider-neutral registered-player path. | Non-HTTP(S) parsed transports remain classified but are not newly enabled; add XMLTV mapping and non-live workflows where source metadata supports them. |
| Xtream Codes API | Provider/content source | **Partially Implemented** | Credential validation; live channels; live/VOD/series categories; movies; Movie detail metadata; Series, Season, and Episode discovery; short EPG; local Live search; typed live/Movie/Episode resolution into `ResolvedPlayback`; and generation-safe non-live UI handoff. The desktop shell exposes Movie detail/play and Series → Season → Episode navigation. | Request builder, API client, DTO translator, adapter, resolver, Movie-detail, season/episode, unified resource/resolution/player contract, registration, desktop-composition, deterministic stale-result/provider-switch/rapid-selection tests, and native Qt flow coverage. | Registered Live, Movie, and Episode resources resolve through the same provider-neutral player path; Series is a browsable container rather than a playable target. | Validate the complete VOD and Series flow against an authorized real Xtream provider; server-side non-live search, richer metadata/presenter styling, and broader provider support remain future work. |
| MAG/Stalker | Provider/content source | **Partially Implemented** | Authorized MAC identity handling; bounded fixed-candidate handshake discovery; failure-safe owned aiohttp-session cleanup; private session state; session refresh; live channels; local search; EPG; live link resolution. | Unit, adapter, integration, credential, session, stream, resolver, EPG, deterministic discovery, lifecycle-cleanup coverage, and a supplied Windows run that recorded safe closure after two failed discovery attempts with no unclosed-session/connector warning. | Live stream resolution is available to the registered-player use case after a selected profile establishes an authenticated session; the supplied Windows run did not reach stream resolution. | An authorized production portal must still yield a structurally valid token-bearing handshake before channel or playback compatibility can be claimed; add categories, VOD, series, archive/catch-up only with verified authorized fixtures. |
| Ministra | Provider/content source | **Planned** | Compatibility assessment and separate-adapter design only. | Assessment documentation only; no runtime adapter. | None. | Obtain authorized sanitized portal fixture and approved device identity; build a separate device-facing adapter. |
| Trusted local plugin SDK | Extensibility | **Implemented** | Explicit local `.py` selection; plugin ID/API-version/namespace checks; transactional provider-factory registration; failure isolation; reference plugin. | Focused loader and reference-plugin tests. | The reference plugin has no real media protocol. | Deliberately excludes sandboxing, signing, marketplace, automatic discovery, remote installation, and auto-updates. |

## Playlist, manifest, EPG, and transport matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| Extended M3U | Playlist format | **Implemented** | Parses `#EXTINF` metadata, validated stream URIs, categories, logos, EPG identifiers, deterministic channel/stream IDs, and adapter-level parsed-stream lookup. | Parser, M3U adapter, and registered-playback integration tests. | Parsed HTTP(S) streams resolve through the provider-neutral registered-player path; non-HTTP(S) transports are not newly enabled. | XMLTV binding and non-live workflows. |
| M3U8/HLS | Manifest format | **Partially Implemented** | Bounded master/media manifest parser with variants, segments, and live/endlist classification. | Focused HLS parser tests. | Decoding/adaptation is delegated to libVLC; no Python adaptive engine. | Player capability negotiation, manifest-fetch workflow, and user-facing diagnostics if required. |
| MPEG-DASH MPD | Manifest format | **Partially Implemented** | Bounded safe MPD parser for live/VOD type and advertised representations. | Focused DASH parser tests. | Decoding/adaptation is delegated to libVLC; no Python adaptive engine. | Player capability negotiation, manifest-fetch workflow, and user-facing diagnostics if required. |
| XMLTV | EPG format | **Partially Implemented** | Bounded `defusedxml` parser with source-channel mapping, size/entry limits, canonical EPG translation, and timezone-aware timestamps. | Focused XMLTV parser tests. | Not a playback concern. | Provider/source configuration, XMLTV fetching, mapping persistence, refresh policy, and UI integration. |
| HTTP | Stream transport | **Partially Implemented** | Canonical URI validation and classification; provider-resolved targets cross the player boundary as ephemeral `ResolvedPlayback`. | Stream URI/protocol, resolved-playback, and VLC transport-option tests. | libVLC receives provider-neutral resolved targets and applies supported typed transport metadata. | Explicit player capability negotiation and operational diagnostics. |
| HTTPS | Stream transport | **Partially Implemented** | Canonical URI validation and classification; provider-resolved targets cross the player boundary as ephemeral `ResolvedPlayback`. | Stream URI/protocol, resolved-playback, and VLC transport-option tests. | libVLC receives provider-neutral resolved targets and applies supported typed transport metadata. | Explicit player capability negotiation and operational diagnostics. |
| HLS | Stream delivery | **Partially Implemented** | URI/manifest classification and bounded parser foundation. | Classification and parser tests. | Relies on libVLC behavior; not negotiated by application code. | End-to-end provider resolution and playback capability reporting. |
| MPEG-DASH | Stream delivery | **Partially Implemented** | URI/manifest classification and bounded parser foundation. | Classification and parser tests. | Relies on libVLC behavior; not negotiated by application code. | End-to-end provider resolution and playback capability reporting. |
| RTMP / RTMPS | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |
| RTSP | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |
| UDP / RTP / SRT | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |

## Content-type matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| Live TV | Content type | **Partially Implemented** | Canonical channels; M3U/Xtream/MAG catalogues; provider-scoped browse/search; registered Xtream live-category discovery; M3U/Xtream/MAG supported HTTP(S) resolution; libVLC orchestration; source-install lifecycle; generic pause/resume/stop controls. | Domain, provider, use-case, resolver, player, lifecycle, integration, and Qt dialog coverage. | All three current provider types have a registered-live component path for supported URLs, with generic playback control feedback. Live-category discovery does not resolve or play content. | Broader transport capability negotiation, category-to-channel navigation, active-item/state detail, and release packaging. |
| Movies/VOD | Content type | **Partially Implemented** | Canonical `Movie`, capability-gated Xtream Movie-detail loading, adapter-local Movie stream resolution, unified target dispatch, explicit desktop Movie detail/play activation, and defensive handling for malformed optional year/rating/artwork metadata. | Domain, API client, translator, adapter, application, target, composition, offscreen Qt, and synthetic Xtream-variation coverage. | Xtream Movie targets resolve through the registered shared-player path; other current providers do not claim Movie playback. | Authorized real-Xtream runtime validation with populated content, richer Movie metadata/presenter styling, and support in other provider adapters. |
| Series | Content type | **Partially Implemented** | Canonical `Series` and provider-scoped `Season`; Xtream Series details, Season discovery, explicit Series → Season desktop navigation, Series year/rating translation, and defensive optional artwork/metadata handling. | Domain, API client, translator, adapter, discovery, composition, offscreen Qt flow, and synthetic Xtream-variation coverage. | Series remains a non-playable container by design. | Authorized real-Xtream runtime validation with populated content and richer Series metadata/presenter styling. |
| Episodes | Content type | **Partially Implemented** | Canonical `Episode`, capability-gated Xtream Episode discovery, adapter-local Episode stream resolution, unified target dispatch, and desktop Episode activation. | Domain, API client, translator, adapter, discovery, target, composition, and offscreen Qt flow coverage. | Xtream Episode targets resolve through the registered shared-player path; other current providers do not claim Episode playback. | Authorized real-Xtream runtime validation, episode metadata enrichment, and support in other provider adapters. |
| EPG | Content type | **Partially Implemented** | MAG and Xtream provider EPG; safe application DTOs; Qt list grid; and registered-provider **local/file XMLTV** source binding with explicit channel mappings and manual refresh. | Adapter, use-case, bounded parser, local-source loader/service, SQLite binding repository, lifecycle-cleanup, and dialog tests. | Not applicable. | Remote/tokenized XMLTV sources, persistent guide-entry cache, scheduled refresh, source discovery, and catch-up linkage. |
| Catch-up/archive | Content type | **Planned** | Capability term only. | No executable capability tests. | None. | Authorized provider fixtures, capability implementations, playback and UI design. |
| Favorites | User library | **Partially Implemented** | Canonical record, SQLite repository, add-selected-channel action, save/list/remove use cases. | Domain, repository, use-case, and channel-browser coverage. | Not applicable. | Favorites screen/list/removal workflow and non-channel content policy. |
| History | User library | **Implemented / Bounded** | Provider-scoped canonical records, SQLite persistence, progress and completion fields, timestamp ordering validation, incomplete Movie/Episode resume restoration, record/list/clear use cases, and bounded library views. | Domain, repository, application, migration, and presentation coverage. | Not applicable. | Per-record deletion, direct replay/navigation, and populated-provider runtime acceptance. |

## Desktop, persistence, and security matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| PySide6/Qt desktop shell | Desktop UI | **Partially Implemented** | Main window, native video surface, provider-entry dialogs, provider list, channel browser, capability-driven Live/Movie/Series catalogue navigation, Movie detail/play activation, Series → Season → Episode navigation, provider-native EPG dialog, local XMLTV configuration/manual-refresh dialog, generic pause/resume/stop and recording actions, settings action, production composition, and supported source-install entry points. | Fake-backed presentation, bootstrap, composition-root, lifecycle, entry-point, category-dialog, XMLTV-dialog, and native offscreen non-live navigation tests. | One shared libVLC player is injected into registered Live, Movie, and Episode playback, playback controls, recording, and the native video surface; Series navigation itself has no direct player path. | Authorized real-Xtream runtime validation, richer metadata presentation, category-to-channel navigation, active-item/state detail, and release packaging. |
| qasync runtime | Desktop lifecycle | **Implemented** | Qt-aware asyncio event loop, lifecycle entry point, generic startup failures, and shared HTTP cleanup after the window loop exits. | Focused runtime and entry-point tests. | Supports asynchronous UI orchestration. | Broader diagnostics and release packaging. |
| libVLC through `python-vlc` | Player backend | **Implemented** | Play, pause, resume, stop, active playback, Qt native output, active `.ts` recording. | Fake-backed adapter and composition tests. | Sole supported player backend. | Track/subtitle controls, capability/error UX, packaging and runtime-discovery validation. |
| Provider registration | Source management | **Implemented for the registered-profile lifecycle** | Secure M3U/Xtream/MAG registration; safe list, type-aware edit, and removal dialogs; metadata persistence/restoration; and production composition. Blank credential edit fields preserve existing keyring values; removal deletes non-secret metadata, the associated keyring entry when present, associated XMLTV binding/mappings, and the runtime registry entry. | Registration, lifecycle, repository, presentation, dialog, bootstrap, and composition-root tests. | Provider resolution remains composed for registered profiles. | Provider diagnostics, confirmation UX, and availability checks. |
| SQLite provider metadata | Persistence | **Implemented** | Non-secret provider ID/type/base URL/active/capability/source-security metadata; initialization, registry restoration, upsert, and deletion in the production composition. Each operation owns, commits or rolls back, and closes its short-lived connection. | Focused repository, lifecycle, composition-root, and connection-closure tests. | Not applicable. | Provider diagnostics. |
| SQLite XMLTV bindings | Persistence | **Implemented for local sources** | Non-secret local path or local `file:` URI plus explicit source-channel to canonical-channel mappings; atomic replacement, retrieval, provider-removal cleanup, and production initialization. No programme entries are persisted. | Domain, repository, local loader/service, application, lifecycle, dialog, bootstrap, and composition-root tests. | Not applicable. | Remote/tokenized source storage, guide-entry cache/retention, and scheduling policy. |
| SQLite favorites/history | Persistence | **Implemented** | Repository implementations and application use cases; production composition initializes both repositories. Each operation owns, commits or rolls back, and closes its short-lived connection. | Focused repository/use-case, composition-root, and connection-closure tests. | Not applicable. | Complete UI. |
| SQLite theme preference | Persistence | **Implemented** | System/light/dark persistence with system fallback; production composition loads preference before Qt bootstrap. | Boundary, engine, dialog, bootstrap, and composition-root tests. | Not applicable. | Optionally apply a newly saved preference immediately. |
| OS keyring | Secret storage | **Implemented** | Provider credential store/retrieve/delete/exists through `keyring`; blank edit fields preserve credentials; provider removal deletes the associated entry; generic error logging; injected into production provider context. | Focused keyring-store, provider-lifecycle, and composition-root tests. | Provider adapters retrieve credentials internally. | Lifecycle and platform packaging verification. |
| Theme/settings | Desktop feature | **Implemented** | System/light/dark value object, SQLite persistence, theme engine, Settings dialog/menu, initial-theme bootstrap, and production-root loading. | Value, persistence, engine, dialog, menu, bootstrap, and composition-root tests. | Not applicable. | Optionally apply a newly saved preference immediately. |
| Stream recording | Desktop feature | **Implemented** | libVLC duplicate display/file output, safe timestamped `.ts` destination, start/stop use cases, generic UI feedback. | Player/use-case/presentation tests. | Active libVLC stream only. | Recording library metadata/listing, conflict policy, and production recording-directory configuration. |

## Quality baseline

The approved recovery and validation increment has passed the deterministic/offscreen gates below. Those checks do not stand in for the configured-but-unexecuted Windows CI native probe or the required authorized Windows desktop runtime gate.

| Check | Result |
|---|---|
| `black --check src tests` | Passed; 310 files unchanged at verification time. |
| `ruff check src tests` | Passed. |
| `mypy src` | Passed; 202 source files checked at verification time. |
| `QT_QPA_PLATFORM=offscreen pytest -q` | Passed; existing non-fatal `aiohttp` bare-handler deprecation warnings remain. |
| `git diff --check` | Passed. |

All deterministic gates are repeated before a handoff or commit decision. A successful offscreen suite must never be reported as successful Windows runtime stream validation.

## Known limitations

1. A production composition root and source-install lifecycle entry point now initialize safe SQLite state, restore provider metadata, wire registered-provider use cases, load the persisted theme, run qasync, report generic startup failures, and close the shared HTTP resource. Packaging, installers, update delivery, crash-reporting policy, and wider operational diagnostics remain incomplete.
2. M3U parsing/catalogue/search and parsed HTTP(S) stream resolution are implemented through the registered-player path. Other classified transports remain outside the current `URL`/player boundary and receive generic safe failures.
3. Xtream now executes registered Movie and Episode stream-resolution/playback plus Series → Season → Episode navigation through narrow declared capabilities. The implementation has not yet been exercised against an authorized real Xtream provider. M3U and MAG/Stalker remain Live-only and do not claim non-live discovery or playback. Non-live search remains local over an explicitly loaded catalogue; it does not add a competing cache or server-side provider search path.
4. MAG/Stalker supports the documented live-TV subset only. The adapter performs a bounded four-candidate discovery before normal session authentication and closes its owned aiohttp session/connector on discovery or authentication failure; a production portal remains unresolved unless one candidate returns a structurally valid token-bearing handshake. VOD, series, categories, archive, and catch-up are not represented as executable adapter capabilities.
5. XMLTV is bound to one registered provider through an explicit local path or local `file:` URI and persisted source-channel mappings; a Qt dialog performs manual bounded refresh. Remote/tokenized XMLTV URLs, a programme-entry cache, scheduled refresh, source discovery, and catch-up linkage remain unimplemented.
6. Favorites/history persistence and bounded library views exist. Provider-scoped Movie/Episode progress, completion, and incomplete-record resume are implemented; per-record deletion and direct replay/navigation remain outside the current contract.
7. Generic pause, resume, and stop actions are available through the existing player port with safe status feedback. The Live-only EOF controller is bounded and deterministic-test covered, but it still requires Windows-native and authorized Windows desktop validation and does not establish a native/libVLC/stream root-cause fix. Registered-provider edit/removal preserves blank credential fields and cleans keyring entries on removal, but confirmation UX, availability diagnostics, detailed player-state semantics, capability negotiation, tracks/subtitles, packaging, update delivery, crash reporting, diagnostics, performance profiling, and release automation are not complete.
8. Ministra requires authorized fixtures and an approved device identity before client code may begin.

## Operational hardening evidence — 2026-08-15

The Linux quality workflow is intentionally a cross-platform validation environment for the real PySide6 offscreen player-shell probes. A supplied Ubuntu 24.04 / Python 3.13 CI run failed before either probe could execute because `libEGL.so.1` was absent while importing PySide6. The workflow now installs only Ubuntu package `libegl1`, verifies the offscreen Qt imports explicitly, and runs the native and 39,753-channel probes directly before coverage pytest. This is classified as a **CI native-runtime dependency omission**, not evidence of a PlayerShell implementation failure. The application dependency list and probe assertions remain unchanged.

The SQLite repositories are operation-scoped rather than long-lived resources. The audit found that `with sqlite3.connect(...)` commits or rolls back a transaction but does not close a connection; this was a **production and test lifecycle defect** affecting provider metadata, favorites, history, theme preference, XMLTV bindings, and one direct test schema-inspection connection. A shared internal helper now commits successful operations, rolls back exceptions, and closes the connection in all paths. All SQLite work continues to open and close inside the same `asyncio.to_thread` worker; there is no `check_same_thread=False`, shared connection, QThread, or event-loop crossing. Focused affected tests pass with `ResourceWarning` promoted to an error.

The MAG runtime issue remains separate and **unresolved pending authorized evidence**. The prior diagnostic release added only safe response-boundary telemetry; no MAG timeout, retry, protocol, response-completeness, provider, playback, qasync, or lifecycle behavior was changed by this operational-hardening increment. Five redacted, unchanged-configuration Windows catalogue runs remain required before classifying intermittent catalogue failure or WinError 995.

The approved VLC-adapter increment adds a bounded, generation- and session-safe recovery controller for **Live** playback only. An unexpected current-session libVLC `END`/`STOPPED`, or a buffering deadline, can rebuild media through the existing media-construction path with at most five attempts in a 45-second window and capped exponential backoff. Explicit stop, shutdown, pause, channel switch, and recording media replacement invalidate recovery work. The controller does not alter providers, MAG behavior, timeouts, network caching, hardware-decoding options, qasync, or `PlayerShell`; it neither proves nor replaces the remaining native libVLC/stream/transport/environment investigation.

| Recovery validation layer | Current evidence | Claim boundary |
|---|---|---|
| Deterministic adapter validation | Focused fake-backed tests cover terminal events, buffering, explicit actions, stale generations, concurrency, stability, bounded attempts, non-live exclusion, and diagnostic redaction. | Proves adapter task ordering and bounded policy only. |
| Full offscreen regression | The full `QT_QPA_PLATFORM=offscreen` suite passes, subject only to existing non-fatal `aiohttp` bare-handler deprecation warnings. | Proves no observed Linux/offscreen regression; it is not a native Windows stream result. |
| Windows CI native validation | The Windows GitHub Actions job installed standard VLC, passed the provider-free lifecycle probe, and passed the deterministic recovery suite as blocking gates. | Proves CI-runner native lifecycle and deterministic controller behavior only; it is not an authorized Live IPTV runtime result. |
| Real Windows desktop runtime | **Not yet executed in this environment.** The current session has no authorized Windows/desktop/native-VLC execution surface. | No claim that a real stream interruption recovers, that the root cause is fixed, or that the failure will reproduce. |

## Security model

- Provider credentials are sensitive and are stored through the OS keyring, not SQLite provider metadata.
- MAG MAC addresses are sensitive device identifiers and are retained through the credential boundary.
- Session tokens/cookies are runtime credentials; adapters keep them volatile and do not persist them in metadata.
- Resolved playback URLs may contain provider access material and must not be stored or displayed unnecessarily.
- Tokenized M3U source URLs are stored securely; metadata retains only a sanitized identifier source.
- XMLTV binding persistence accepts only local paths or local `file:` URIs and explicit non-secret channel mappings. Remote/tokenized XMLTV sources are rejected; source text is never shown in status feedback.
- Logs, status text, metadata, and test fixtures must not expose credentials, MAC addresses, tokens, or resolved stream URLs.
- Provider DTOs must be translated into canonical records rather than propagated into application or presentation layers.
- Trusted local plugins are executable Python and are not sandboxed; users must enable only plugins they trust.

## Next milestone

### Authorized Windows Live EOF Recovery Runtime Gate

**Objective:** Validate the implemented bounded Live recovery controller in the authorized Windows desktop application without changing provider configuration, MAG behavior, credentials, stream selection, VLC options, caching, hardware-decoding settings, timeouts, qasync, or `PlayerShell`.

The runtime observation must distinguish normal Live playback, a failure that does not reproduce, a bounded recovery that returns to `PLAYING`, bounded recovery exhaustion, and a recovery-controller defect. It must also verify that channel switching and explicit stop cannot resurrect a stale channel. This gate may not be represented as complete until it has actually run against the real desktop application and authorized live environment.

### Subsequent usability milestone — Live-TV Workflow Completion

**Objective:** Complete the highest-value live-TV usability gaps now that M3U, Xtream, and MAG resolve supported live streams through the registered-player path.

**Delivered increment:** M3U now uses fresh parsed-playlist lookup for the selected canonical channel, advertises `STREAM_RESOLUTION`, converts only supported HTTP(S) stream URIs to the current player `URL` value object, and returns generic failures for unknown channels or unsupported transport boundaries. Adapter and resolver-to-player integration tests confirm the path without source URL disclosure.

**Delivered increment:** Pause, resume, and stop now use dedicated application use cases that delegate only through `PlayerPort`. The Qt Playback menu invokes them on qasync, emits generic success/failure status text, and shares the same libVLC player used by registered playback and recording. Detailed state semantics are not inferred in the UI because the current player port exposes only `is_playing` rather than a full paused/stopped state model.

**Delivered increment:** Registered-provider lifecycle management now supports safe type-aware edit and removal workflows. Update requests retain credentials when optional fields are blank; non-secret metadata is persisted before registry refresh; removal deletes persisted metadata, deletes the matching OS-keyring credential if present, and then removes the runtime registry record. The provider list refreshes after removal and reports only generic feedback.

**Delivered increment:** Registered Xtream live categories now flow from the provider registry through the factory, typed `CategoryProvider`, canonical `Category` translation, registered resolver, `LoadCategories` use case, and a minimal Qt browse dialog. The dialog displays category names only, supports provider selection, handles empty and error states safely, and does not select content, resolve streams, or invoke the player.

**Delivered increment:** Registered providers can now configure one local path or local `file:` XMLTV source with explicit source-channel mappings. SQLite persists only that non-secret binding; manual refresh uses the bounded `defusedxml` parser and renders title/time rows through a Qt dialog. Provider removal deletes the associated binding. Remote/tokenized sources, cached programme persistence, scheduled refresh, and all playback paths remain excluded.

**Next bounded task:** Validate the completed Player 3 hardening against an authorized populated Xtream account and a Windows-native environment; do not promote synthetic or Linux/offscreen evidence into those acceptance categories.

## Related documents

| Document | Purpose |
|---|---|
| [README.md](README.md) | Product overview, setup, architecture summary, and contributor orientation. |
| [ROADMAP.md](ROADMAP.md) | Historical milestone mapping and prioritized delivery direction. |
| [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md) | P0–P3 product gaps and prioritization rationale. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current dependency boundaries and terminology. |
| [SECURITY.md](SECURITY.md) | Security policy and the current repository security model. |
| [MINISTRA_COMPATIBILITY_ASSESSMENT.md](MINISTRA_COMPATIBILITY_ASSESSMENT.md) | Historical, date-scoped Ministra decision gate and implementation prerequisites. |


## User-library increment — 2026-08-13

**Implemented:** Favorites library listing with empty state, refresh, generic error feedback, and single-record removal; History recent listing with duration, persisted playback position, watched timestamp, refresh, generic error feedback, and confirmation-protected clear-all; production SQLite wiring and Qt Library menu actions.

**Not implemented:** History per-record deletion, replay, resume, provider reconstruction, stream reconstruction, a new playback-position model, and a new player resume API.


## Xtream/MAG compatibility audit update

The normalized provider model set now includes secret-free `ProviderSession`, `AccountInfo`, `ServerInfo`, and `CatchupEvent` records. Xtream account and server metadata are executable through explicit capability ports and resolver methods, with deterministic tests covering active, expired, unknown, malformed, and sparse response variations. The existing Xtream Live/VOD/Series/EPG/search/playback workflows remain intact. MAG retains its verified live/session/EPG/search/playback capability declaration; MAG VOD, Series, and executable catch-up remain unsupported because the current legacy facade and authorized fixtures do not establish those contracts.

The complete offscreen test suite with coverage, native Qt/player probe, Ruff, Black, mypy, and `git diff --check` all pass after this update. Coverage is reported as an evidence metric rather than a release threshold; no backend or player contract was changed.


## KiddaC technology adaptation status

The EStalker and XStreamity source studies are complete and are recorded in `KIDDAC_TECHNOLOGY_GAP_MATRIX.md` and the adaptation documentation. The safe implementation increment is intentionally narrow: the existing Xtream/MAG normalized provider boundaries remain authoritative, and Movie/Series catalogues now provide local category/search/sort controls over loaded canonical snapshots. The default sort preserves provider response order; title, newest, and rating ordering are explicit local choices that do not issue provider requests.

EStalker Enigma2 UI/global state/service APIs, fabricated device identities, raw credential-bearing timeshift URLs, and unverified handshake tricks remain rejected. Catch-up, hidden-content policy, TMDB-style enrichment, and broad provider failover remain documented partial or blocked areas rather than unsupported claims. The prior Live-only EOF recovery policy and shared PlayerPort/libVLC boundary are unchanged.


## Product-hardening and reference-study update — 2026-08-16

The current origin/main implementation was traced end-to-end from qasync startup and production composition through provider registration, capability-gated resolution, canonical translation, PlayerShell, `ResolvedPlayback`, the shared libVLC `PlayerPort`, SQLite/keyring persistence, and shutdown. The trace is recorded in the final audit report and confirms that Xtream Movie and Episode playback, Series → Season → Episode discovery, local catalogue search/category filtering/sorting, provider switching, stale-result protection, favorites/history bounded library views, and Live-only recovery remain within their stated boundaries.

The evidence-backed implementation increment is intentionally small: deterministic sanitized Xtream fixtures now distinguish expired authentication from an active account with zero VOD/Series content and preserve a safe unusual `webm` container extension. No provider or player contract was changed. Public EStalker and XStreamity projects are acknowledged in `README.md`; no source code was copied, no new dependency was added, and no license or endorsement claim is made where repository metadata did not expose an explicit license.

The focused verification set passed: 75 tests, the deterministic native PlayerShell probe, and the 100,000-record local catalogue performance probe. The full quality-gate suite remains the required final check. The following remain not executed or not established: authorized populated real-Xtream runtime validation, authorized MAG production compatibility, authorized Windows desktop Live EOF runtime, executable catch-up, replay/resume reconstruction, remote XMLTV caching/scheduling, and audio/subtitle track selection.

## Commercial Xtream VOD/Series increment — 2026-08-16

The current Xtream non-live status is **Partially Implemented with a materially improved detail experience**. Movie and Series metadata now has a safe optional path from provider payload through canonical entities and presentation DTOs into an inline detail panel. The panel is covered by a native offscreen PlayerShell probe and does not claim remote artwork loading, resume reconstruction, or catch-up.

| Area | Current classification | Evidence and boundary |
|---|---|---|
| Movie catalogue/detail | **IMPLEMENTED / PARTIAL** | Synthetic rich-metadata translator and application tests, native detail-panel assertions, and full suite pass. Populated authorized real-provider validation is not executed. |
| Series/season/episode navigation | **IMPLEMENTED / PARTIAL** | Existing generation-safe Series → Season → Episode flow plus metadata/count propagation and episode duration mapping are covered synthetically. Series containers remain non-playable. |
| Search/category/sort | **IMPLEMENTED** | Existing local loaded-snapshot controls and native/performance probes remain green; no provider request is introduced. |
| Artwork | **PARTIAL / DEFERRED** | Provider poster/backdrop metadata is retained and availability is shown; network loading, bounded disk/memory cache, and fallback policy remain deferred. |
| Favorites/history/resume | **IMPLEMENTED / PARTIAL** | Existing SQLite Favorites/History bounded library behavior is preserved. Replay/resume reconstruction and per-record deletion remain unimplemented. |
| Playback | **IMPLEMENTED for existing eligible targets** | Existing Movie/Episode resolution and shared libVLC handoff are regression-tested. No fake resume or new track APIs were added. |
| Real-provider evidence | **BLOCKED BY EVIDENCE** | The authorized provider session previously returned zero VOD/Series records; no populated runtime claim is made. |

Verification for this increment consists of the full offscreen pytest suite with 8,176 statements measured at 74% coverage, native PlayerShell and VLC lifecycle probes, the 100,000-record performance probe, Ruff, Black, mypy, and `git diff --check`; all passed in the final local run.


## Advanced Xtream VOD/Series increment — 2026-08-16

The advanced audit increment is complete within the existing architecture. Movie and Series DTOs now expose provider-supplied optional metadata including genre, director, cast, country, release date, duration, backdrop, container extension, and Series counts. PlayerShell renders richer inline detail summaries, bounded artwork placeholders/previews, local metadata search, explicit loading/empty/error states, Movie/Series Favorite actions, and safe Series → Season → Episode detail navigation. Episode Favorite remains unavailable because the existing Favorite contract excludes episodes.

A shared-session `BoundedArtworkLoader` is injected from production composition. It validates non-secret HTTP(S) artwork URLs, limits individual and aggregate cache memory, expires entries, evicts LRU entries, invalidates by provider, preserves cancellation, and rejects malformed or oversized responses. Native Qt tests prove successful decode, placeholder behavior, and provider invalidation. Provider-scoped Favorites are persisted with a nullable SQLite migration for legacy rows and idempotent same-provider saves.

| Capability | Classification | Evidence |
|---|---|---|
| Movie/Series details and metadata | IMPLEMENTED | Native Qt probe and full pytest with rich sanitized fixtures. |
| Local search, category/filter, sort | IMPLEMENTED | Native probe, application tests, and 100,000-record performance probe. |
| Artwork preview and bounded cache | IMPLEMENTED | Focused loader tests, shared binary HTTP test, native image decode probe. |
| Favorites | IMPLEMENTED / PARTIAL | Provider-scoped persistence and duplicate prevention are tested; direct replay/navigation and Episode Favorites remain outside existing contracts. |
| History | PARTIAL | Existing SQLite listing, progress display, and clear-all remain; provider enrichment and direct replay are not implemented. |
| Watched state and true resume | DEFERRED / BLOCKED BY CONTRACT | `PlayerPort` lacks typed position/seek/read capabilities and History lacks provider/completion/upsert semantics. |
| Real populated-provider acceptance | BLOCKED BY EVIDENCE | The authorized validation session previously returned zero VOD/Series records. |
| Catch-up, tracks, external metadata enrichment | DEFERRED / PROVIDER-DEPENDENT | No approved provider-neutral capability or credential/licensing contract exists. |

All implementation boundaries explicitly preserve Live EOF recovery, MAG, M3U, shared libVLC ownership, qasync task ownership, and stale-result protection.


## Real Xtream acceptance and production-hardening audit — 2026-08-16

The subsequent acceptance phase performed a read-only protocol review, controlled credential-availability check, response-robustness verification, artwork/Favorites hardening verification, PlayerPort capability audit, commercial native UX audit, concurrency matrix, and exact 10K/50K/100K performance checkpoints. The current implementation remains **READY for synthetic/native acceptance and PARTIAL for populated real-provider acceptance**.

No authorized populated Xtream account was available in the current environment. The prior authorized session authenticated but returned zero VOD and zero Series records, so populated real-provider acceptance remains **BLOCKED BY EVIDENCE**. Windows validation is **NOT EXECUTED** because the current environment is Linux; the Windows-only VLC probe correctly reports `SKIP reason=windows_required`.

The PlayerPort capability boundary remains intentionally narrow: play, pause, resume, stop, recording, native output attachment, and boolean playing/recording state are supported. Seek, position, duration, completion, audio tracks, subtitle tracks, volume, mute, and typed fullscreen capabilities remain unsupported or deferred. Watched/resume is not implemented.

The exact performance matrix passed at 10,000, 50,000, and 100,000 records for channel, Movie, and Series replacement, selection identity, filter, search, no-match, and clear-search behavior. The concurrency matrix passed 50 tests covering stale selection, provider switching, cancellation, playback, artwork, shutdown, and task ownership.

## Player 2 commercial playback status — 2026-08-16

Player 2 is implemented across the preserved application, VLC infrastructure, Qt presentation, and SQLite history boundaries. The typed PlayerPort capability model now covers state, position, duration, seeking, volume, mute, native audio/subtitle tracks, restart, and aspect ratio. PlayerShell provides mode-aware commercial controls, with Live seek and resume intentionally disabled.

History now persists provider-scoped identity, runtime progress, watched percentage, lifecycle timestamps, and completion through a backward-compatible SQLite migration. Resume is restricted to incomplete Movie and Episode records with matching provider identity. Deterministic tests, source quality gates, offscreen PlayerShell probes, and 10K/50K/100K performance checkpoints pass.

The Windows-only native VLC probe is **NOT EXECUTED** on Linux and reports an explicit platform skip. Populated authorized-provider acceptance is **NOT EXECUTED**. These remain open validation actions and are not converted into implementation claims. See [`docs/PLAYER_2_RUNTIME_VALIDATION.md`](docs/PLAYER_2_RUNTIME_VALIDATION.md) and [`PLAYER_2_FINAL_AUDIT.md`](PLAYER_2_FINAL_AUDIT.md).


## Player 3 commercial hardening status — 2026-08-16

Player 3 is **implemented and deterministically validated** within the preserved Player 2 architecture. The increment hardens individual-record tolerance in Xtream live/VOD/Series/Season/Episode translation, declares MAG live categories, preserves EPG description/category metadata with a bounded DTO list, adds provider-scoped adjacent-episode controls, maps typed backend states to safe presentation labels, enforces History timestamp ordering, and centralizes credential-free user error messages. No provider URL construction, credential access, libVLC import, qasync replacement, Live EOF recovery rewrite, or provider architecture rewrite was introduced.

| Evidence area | Result | Claim boundary |
|---|---|---|
| Focused Player 3 regression suite | **PASS** | Modified domain, application, provider, presentation, migration, and synthetic-variation behavior passed. |
| Isolated Qt concurrency/lifecycle matrix | **PASS** | Compatible Qt-heavy modules passed when run in isolated invocations; a combined offscreen invocation can segfault during cross-module Qt teardown and is not used as a product-failure claim. |
| Performance probe | **PASS** | 39,753 live records, 5,000 content records, and dynamic catalogue sizes 0, 1, 10, 100, 500, 1,000, 5,000, 10,000, 17,431, 39,753, 50,000, and 100,000 were exercised. |
| Changed-file security scan | **PASS** | No known authorized-provider literals or quoted secret assignments in changed source/docs; `git diff --check` passed. |
| Linux native classification | **PASS / LIMITED** | PlayerShell native probe exited successfully; VLC lifecycle probe reported `SKIP reason=windows_required`; the environment has no VLC binary. |
| Windows-native validation | **NOT EXECUTED** | The current environment is Linux. |
| Populated authorized Xtream acceptance | **NOT EXECUTED** | No real-provider sequence was run in this session; synthetic fixtures are not promoted to provider evidence. |
| MAG VOD/Series/Episodes | **NOT EXECUTED** | The authorized portal contract remains blocked before a compatible non-live capability can be claimed. |
| Catch-up/archive | **NOT IMPLEMENTED** | No current provider advertises `ProviderCapability.CATCHUP`; no fake resolver or UI was added. |

The authoritative detailed record is [PLAYER_3_FINAL_AUDIT.md](PLAYER_3_FINAL_AUDIT.md). The controlled real-provider procedure is [docs/PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md](docs/PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md), and the architecture/runtime evidence supplements are [docs/PLAYER_3_ARCHITECTURE.md](docs/PLAYER_3_ARCHITECTURE.md) and [docs/PLAYER_3_RUNTIME_VALIDATION.md](docs/PLAYER_3_RUNTIME_VALIDATION.md).
