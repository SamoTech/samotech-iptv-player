# Project Status — Authoritative Current State

> **Authority:** This document is the sole source of truth for what the repository currently implements, partially implements, and plans. [README.md](README.md) summarizes this state for users and contributors. [ROADMAP.md](ROADMAP.md) explains historical delivery and future direction. Historical reports and assessments are records of their stated date and commit, not current-state authority.

**Product:** SamoTech IPTV Player
**Package version:** `0.1.0`
**Current baseline:** The `main` revision containing the approved bounded Live EOF recovery and Windows validation increment; use `git rev-parse HEAD` for its immutable revision identifier.
**Current product milestone:** Xtream VOD and Series workflow — **implemented and deterministically validated with synthetic variation fixtures; authorized real-Xtream runtime evidence remains partial/pending populated content**. Non-live PlayerShell handlers now reject stale provider/content/action generations, provider switches, navigation changes, duplicate actions, and disposed-owner completions before state or playback mutation. The prior bounded Live EOF recovery remains implemented, locally validated, and Windows-CI validated; its authorized Windows runtime gate remains pending.
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
| History | User library | **Partially Implemented** | Canonical record, SQLite repository, record/list/clear use cases; playback record invocation. | Domain, repository, and use-case coverage. | Not applicable. | History UI, accurate playback progress/state updates, resume behavior. |

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
6. Favorites/history persistence exists, but full library management UI and resume behavior do not.
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

**Next bounded task:** Complete the existing favorites/history user-library foundations with safe list, removal, and history views before considering resume or non-live playback behavior.

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
