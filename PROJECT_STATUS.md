# Project Status — Authoritative Current State

> **Authority:** This document is the sole source of truth for what the repository currently implements, partially implements, and plans. [README.md](README.md) summarizes this state for users and contributors. [ROADMAP.md](ROADMAP.md) explains historical delivery and future direction. Historical reports and assessments are records of their stated date and commit, not current-state authority.

**Product:** SamoTech IPTV Player
**Package version:** `0.1.0`
**Current baseline commit:** `7896c9e5036d278b68ffc5e1cde35b8015415707` (`feat: add theme settings UI`)
**Current product milestone:** Runnable Desktop Composition and Provider Lifecycle
**Baseline verified:** 2026-08-12 UTC+03:00

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
Authorized stream resolution
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

## Status vocabulary

| Status | Definition |
|---|---|
| **Implemented** | Executable through the stated layer and covered by focused tests. It may still await the lifecycle milestone before it is reachable from a supported end-user launcher. |
| **Partially Implemented** | A real, tested subset or foundation exists, but an essential workflow, capability, integration, or user-facing exposure remains absent. |
| **Planned** | No executable support claim is made. Research, an enum value, or an abstract interface alone is not implementation. |

## Provider and content-source matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| M3U source | Provider/content source | **Partially Implemented** | Local, `file:`, and HTTP(S) source loading; extended-M3U parsing; protected tokenized source storage; canonical live channels; local search. | Source loader, parser, adapter, registration, and transport coverage. | Not through the registered-provider path: the adapter does not implement `PlaybackProvider`. | Add canonical parsed-stream lookup and resolution; bind to registered playback; add source-to-XMLTV mapping and non-live workflows where source metadata supports them. |
| Xtream Codes API | Provider/content source | **Partially Implemented** | Credential validation; live channels; live/VOD/series categories; movies; series; short EPG; local live-channel search; live stream URL construction/resolution. | Request builder, API client, DTO translator, adapter, resolver, registration, and EPG coverage. | Live stream resolution is available to the registered-player use case; no desktop VOD/series workflow. | Add resolver/use-case/UI support for categories, movies, series, episodes, VOD playback, and provider lifecycle UX. |
| MAG/Stalker | Provider/content source | **Partially Implemented** | Authorized MAC identity handling; private session state; session refresh; live channels; local search; EPG; live link resolution. | Unit, adapter, integration, credential, session, stream, resolver, and EPG coverage. | Live stream resolution is available to the registered-player use case. | Add categories, VOD, series, archive/catch-up only with verified authorized fixtures; complete user-facing management. |
| Ministra | Provider/content source | **Planned** | Compatibility assessment and separate-adapter design only. | Assessment documentation only; no runtime adapter. | None. | Obtain authorized sanitized portal fixture and approved device identity; build a separate device-facing adapter. |
| Trusted local plugin SDK | Extensibility | **Implemented** | Explicit local `.py` selection; plugin ID/API-version/namespace checks; transactional provider-factory registration; failure isolation; reference plugin. | Focused loader and reference-plugin tests. | The reference plugin has no real media protocol. | Deliberately excludes sandboxing, signing, marketplace, automatic discovery, remote installation, and auto-updates. |

## Playlist, manifest, EPG, and transport matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| Extended M3U | Playlist format | **Implemented** | Parses `#EXTINF` metadata, validated stream URIs, categories, logos, EPG identifiers, and deterministic channel/stream IDs. | Parser and M3U adapter tests. | Parsed streams are modeled but M3U provider playback resolution is missing. | Add adapter-level stream lookup/resolution and application exposure. |
| M3U8/HLS | Manifest format | **Partially Implemented** | Bounded master/media manifest parser with variants, segments, and live/endlist classification. | Focused HLS parser tests. | Decoding/adaptation is delegated to libVLC; no Python adaptive engine. | Player capability negotiation, manifest-fetch workflow, and user-facing diagnostics if required. |
| MPEG-DASH MPD | Manifest format | **Partially Implemented** | Bounded safe MPD parser for live/VOD type and advertised representations. | Focused DASH parser tests. | Decoding/adaptation is delegated to libVLC; no Python adaptive engine. | Player capability negotiation, manifest-fetch workflow, and user-facing diagnostics if required. |
| XMLTV | EPG format | **Partially Implemented** | Bounded `defusedxml` parser with source-channel mapping, size/entry limits, canonical EPG translation, and timezone-aware timestamps. | Focused XMLTV parser tests. | Not a playback concern. | Provider/source configuration, XMLTV fetching, mapping persistence, refresh policy, and UI integration. |
| HTTP | Stream transport | **Partially Implemented** | Canonical URI validation and classification. | Stream URI/protocol tests. | libVLC receives provider-resolved URLs. | Explicit player capability negotiation and operational diagnostics. |
| HTTPS | Stream transport | **Partially Implemented** | Canonical URI validation and classification. | Stream URI/protocol tests. | libVLC receives provider-resolved URLs. | Explicit player capability negotiation and operational diagnostics. |
| HLS | Stream delivery | **Partially Implemented** | URI/manifest classification and bounded parser foundation. | Classification and parser tests. | Relies on libVLC behavior; not negotiated by application code. | End-to-end provider resolution and playback capability reporting. |
| MPEG-DASH | Stream delivery | **Partially Implemented** | URI/manifest classification and bounded parser foundation. | Classification and parser tests. | Relies on libVLC behavior; not negotiated by application code. | End-to-end provider resolution and playback capability reporting. |
| RTMP / RTMPS | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |
| RTSP | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |
| UDP / RTP / SRT | Stream transport | **Partially Implemented** | URI validation and classification. | Stream protocol tests. | No provider-specific supported playback claim. | Runtime player capability validation and provider workflow coverage. |

## Content-type matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| Live TV | Content type | **Partially Implemented** | Canonical channels; M3U/Xtream/MAG catalogues; provider-scoped browse/search; Xtream/MAG resolution; libVLC orchestration. | Domain, provider, use-case, player, and Qt dialog coverage. | Xtream and MAG registered-live paths exist as components; no production launcher. | Composition root/CLI lifecycle; M3U resolver; controls/state UX. |
| Movies/VOD | Content type | **Partially Implemented** | Domain `Movie`; Xtream adapter `load_movies()`. | Domain and Xtream adapter/translator tests. | No registered movie-playback route or UI. | Catalogue resolver/use cases, VOD URL resolution, browse/playback UI. |
| Series | Content type | **Partially Implemented** | Domain `Series`/`Episode`; Xtream adapter `load_series()`. | Domain and Xtream adapter/translator tests. | No series/episode playback workflow. | Series detail/episode endpoints, resolver/use cases, and UI. |
| Episodes | Content type | **Partially Implemented** | Canonical domain record and validation. | Domain tests. | None. | Provider translation, catalogue browsing, episode stream resolution, UI. |
| EPG | Content type | **Partially Implemented** | MAG and Xtream provider EPG; safe application DTOs; Qt list grid; XMLTV parser foundation. | Adapter, use-case, parser, and dialog tests. | Not applicable. | XMLTV provider binding, refresh/cache strategy, and catch-up linkage. |
| Catch-up/archive | Content type | **Planned** | Capability term only. | No executable capability tests. | None. | Authorized provider fixtures, capability implementations, playback and UI design. |
| Favorites | User library | **Partially Implemented** | Canonical record, SQLite repository, add-selected-channel action, save/list/remove use cases. | Domain, repository, use-case, and channel-browser coverage. | Not applicable. | Favorites screen/list/removal workflow and non-channel content policy. |
| History | User library | **Partially Implemented** | Canonical record, SQLite repository, record/list/clear use cases; playback record invocation. | Domain, repository, and use-case coverage. | Not applicable. | History UI, accurate playback progress/state updates, resume behavior. |

## Desktop, persistence, and security matrix

| Technology | Category | Current status | Implemented | Tested | Playback | Remaining work |
|---|---|---:|---|---|---|---|
| PySide6/Qt desktop shell | Desktop UI | **Partially Implemented** | Main window, native video surface, provider-entry dialogs, provider list, channel browser, EPG dialog, recording actions, settings action, and a production composition root that wires the existing application graph. | Fake-backed presentation, bootstrap, and composition-root tests. | One shared libVLC player is injected into registered-provider playback, recording, and the native video surface. | Executable launcher, startup/shutdown lifecycle ownership, user-facing playback controls/state. |
| qasync runtime | Desktop lifecycle | **Partially Implemented** | Qt-aware asyncio event loop and main-window show/run boundary. | Focused runtime test. | Supports asynchronous UI orchestration. | Production entry point, startup error handling, initialization/close lifecycle. |
| libVLC through `python-vlc` | Player backend | **Implemented** | Play, pause, resume, stop, active playback, Qt native output, active `.ts` recording. | Fake-backed adapter and composition tests. | Sole supported player backend. | Track/subtitle controls, capability/error UX, packaging and runtime-discovery validation. |
| Provider registration | Source management | **Partially Implemented** | Secure M3U/Xtream/MAG registration; metadata persistence/restoration through the production composition root; safe provider list. | Registration, repository, dialog, and composition-root tests. | Provider resolution is now composed for registered profiles. | Edit/remove flows, credential cleanup, and user diagnostics. |
| SQLite provider metadata | Persistence | **Implemented** | Non-secret provider ID/type/base URL/active/capability/source-security metadata; repository initialization and registry restoration in production composition. | Focused repository and composition-root tests. | Not applicable. | Lifecycle-owned shutdown and provider management UI. |
| SQLite favorites/history | Persistence | **Implemented** | Repository implementations and application use cases; production composition initializes both repositories. | Focused repository/use-case and composition-root tests. | Not applicable. | Complete UI and lifecycle-owned shutdown. |
| SQLite theme preference | Persistence | **Implemented** | System/light/dark persistence with system fallback; production composition loads preference before Qt bootstrap. | Boundary, engine, dialog, bootstrap, and composition-root tests. | Not applicable. | Optionally apply a newly saved preference immediately. |
| OS keyring | Secret storage | **Implemented** | Provider credential store/retrieve/delete/exists through `keyring`; generic error logging; injected into production provider context. | Focused keyring-store and composition-root tests. | Provider adapters retrieve credentials internally. | Lifecycle and platform packaging verification. |
| Theme/settings | Desktop feature | **Implemented** | System/light/dark value object, SQLite persistence, theme engine, Settings dialog/menu, initial-theme bootstrap, and production-root loading. | Value, persistence, engine, dialog, menu, bootstrap, and composition-root tests. | Not applicable. | Optionally apply a newly saved preference immediately. |
| Stream recording | Desktop feature | **Implemented** | libVLC duplicate display/file output, safe timestamped `.ts` destination, start/stop use cases, generic UI feedback. | Player/use-case/presentation tests. | Active libVLC stream only. | Recording library metadata/listing, conflict policy, and production recording-directory configuration. |

## Quality baseline

The latest full quality gate was run on commit `7896c9e5036d278b68ffc5e1cde35b8015415707` before this documentation rebaseline.

| Check | Result |
|---|---|
| `black --check src tests` | Passed; 233 files unchanged at verification time. |
| `ruff check src tests` | Passed. |
| `mypy src` | Passed in strict mode; 164 source files checked at verification time. |
| `pytest -q` | Passed. |
| `git diff --check` | Passed. |

The documentation rebaseline must run the same quality gate before publication. Source/test counts should be reported from that final run rather than assumed from this baseline.

## Known limitations

1. A production composition root now initializes safe SQLite state, restores provider metadata, wires registered-provider use cases, loads the persisted theme, and shares one libVLC player. There is still no CLI entry point or complete startup/shutdown lifecycle, so this is not yet a supported runnable product path.
2. M3U parsing/catalogue/search is implemented, but the M3U adapter does not currently resolve parsed streams through the registered-player path.
3. Xtream VOD, series, category-family methods are adapter capabilities without registered-provider resolver/use-case/desktop catalogue workflows.
4. MAG/Stalker supports the documented live-TV subset only; VOD, series, categories, archive, and catch-up are not represented as executable adapter capabilities.
5. XMLTV parsing is not bound to a provider source, mapping store, refresh job, or desktop workflow.
6. Favorites/history persistence exists, but full library management UI and resume behavior do not.
7. Player capability negotiation, tracks/subtitles, player-state UX, packaging, update delivery, crash reporting, diagnostics, performance profiling, and release automation are not complete.
8. Ministra requires authorized fixtures and an approved device identity before client code may begin.

## Security model

- Provider credentials are sensitive and are stored through the OS keyring, not SQLite provider metadata.
- MAG MAC addresses are sensitive device identifiers and are retained through the credential boundary.
- Session tokens/cookies are runtime credentials; adapters keep them volatile and do not persist them in metadata.
- Resolved playback URLs may contain provider access material and must not be stored or displayed unnecessarily.
- Tokenized M3U source URLs are stored securely; metadata retains only a sanitized identifier source.
- Logs, status text, metadata, and test fixtures must not expose credentials, MAC addresses, tokens, or resolved stream URLs.
- Provider DTOs must be translated into canonical records rather than propagated into application or presentation layers.
- Trusted local plugins are executable Python and are not sandboxed; users must enable only plugins they trust.

## Next milestone

### Runnable Desktop Composition and Provider Lifecycle

**Objective:** Compose the existing tested components into a safe, launchable application lifecycle.

**Why it is next:** It makes the provider → stream → libVLC → Qt live-TV workflow usable by real users. It is a P0 product blocker and a prerequisite for reliable provider management, packaging, diagnostics, updates, and production hardening.

**Dependencies:** Existing configuration provider; SQLite metadata/favorite/history/theme repositories; OS keyring; provider registry/factory/context; M3U/Xtream/MAG registrations; application use cases; `build_desktop_application()`; `run_desktop_application()`; qasync and libVLC runtime availability.

**Delivered increment:** `build_production_desktop_application()` now initializes non-secret SQLite repositories, restores metadata into the registry, registers M3U/Xtream/MAG factories, constructs provider services and existing use cases, loads the persisted initial theme, builds one libVLC player, and returns the existing `DesktopApplication`. Fake-backed integration coverage verifies safe metadata restoration, provider registrations, theme loading, and shared-player wiring.

**Next bounded task:** Add a production module/CLI entry point and lifecycle owner that invokes this composition root, runs the qasync desktop loop, emits only generic startup failures, and closes lifecycle-managed resources safely.

## Related documents

| Document | Purpose |
|---|---|
| [README.md](README.md) | Product overview, setup, architecture summary, and contributor orientation. |
| [ROADMAP.md](ROADMAP.md) | Historical milestone mapping and prioritized delivery direction. |
| [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md) | P0–P3 product gaps and prioritization rationale. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current dependency boundaries and terminology. |
| [SECURITY.md](SECURITY.md) | Security policy and the current repository security model. |
| [MINISTRA_COMPATIBILITY_ASSESSMENT.md](MINISTRA_COMPATIBILITY_ASSESSMENT.md) | Historical, date-scoped Ministra decision gate and implementation prerequisites. |
