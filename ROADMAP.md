# Roadmap

## Current project status

The repository scaffold and the core recovery are complete. The recovered core is installable, has a single configuration boundary, uses domain-oriented provider ports, includes a tested MAG/Stalker adapter, and passes the configured test, type, and lint checks.

> **Current phase:** Phase 9 — theme engine, dark/light styles, and settings UI — **completed**.
> **Completed milestone:** Core recovery; validated domain/provider contracts; VLC and Qt desktop composition; registered-provider channel browsing, search, favorites, watch history, EPG, and recording; bounded secure XMLTV parsing; an explicitly enabled trusted local provider-plugin SDK with a reference plugin and transactional factory registration; and persisted system/light/dark theme preferences with Qt startup application and a Settings menu.
> **Next product milestone:** Auto-updater, crash reporting, picture-in-picture, and subtitle/audio management.

| Phase | Scope | Status |
|---:|---|---|
| **Recovery** | Packaging repair; configuration composition; canonical provider ports; MAG adapter/credential/session ownership; integration coverage; strict quality gate; truthful documentation | **Completed** |
| **1** | Repository scaffold, baseline architecture, CI configuration, module placeholders | **Completed** |
| **2** | Complete domain entities and value objects; M3U parser; parser and domain unit tests | **Completed** — extended-M3U parser plus focused validation coverage for all current domain records and value objects are delivered; M3U provider-adapter integration is deferred to provider-management work |
| **3** | VLC/player adapter, SQLite repositories, dependency-injection composition root, and basic window | **Completed** |
| **4** | Channel browser UI, search, favorites, and watch history | **Completed** |
| **5** | Xtream Codes and Stalker provider clients; playlist manager UI | Partially advanced by recovered MAG/Stalker core, M3U/Xtream capability increments, and a Ministra separate-provider assessment; Ministra implementation remains gated on an authorized fixture and approved device identity |
| **6** | XMLTV EPG parser and EPG grid view | **Completed** — registered-provider EPG capability resolution, safe application DTOs, a Qt grid that displays title/start/end only, and a bounded `defusedxml` parser with explicit source-channel mapping and canonical `EPGEntry` translation are delivered; source fetching and provider-specific XMLTV binding remain future integration work |
| **7** | Stream recording through the player adapter and recording UI | **Completed** — libVLC duplicate display/file stream output, safe timestamped `.ts` destinations, start/stop application use cases, and Qt Playback-menu controls are delivered; recording-library metadata management remains future work |
| **8** | Plugin SDK, example provider plugin, and plugin loader | **Completed** — API version 1 defines trusted local plugins selected explicitly by path and ID, a narrow host-owned factory-registration context, namespace/API validation, transactional activation, generic failure isolation, loader tests, and a reference plugin; sandboxing, signing, remote install, and automatic discovery remain deliberately out of scope |
| **9** | Theme engine, dark/light styles, and settings UI | **Completed** — a non-secret SQLite-backed `ThemePreference` supports system, light, and dark choices; deterministic Qt application styles are applied at desktop startup; and the Qt Settings menu opens a safely validated, persisted preference dialog. |
| **10** | Auto-updater, crash reporting, picture-in-picture, subtitle/audio management | Planned |
| **11** | Performance pass, memory profiling, and large-playlist stress testing | Planned |
| **12** | PyInstaller packaging, Windows installer, and release automation | Planned |

## Provider and protocol support matrix

> **Status convention:** An integration is marked **Implemented** only where executable processing through its stated layer and focused tests exist. **Partially implemented** records a functioning subset; **Planned** indicates that no executable support claim is made.

| Integration | Architecture | Parser/API | Domain translation | Tests | Player backend | Status |
|---|---|---|---|---|---|---|
| M3U playlist | Capability-oriented provider adapter | Local-file and HTTP(S) source loader plus extended-M3U parser; XMLTV source-to-channel binding is not yet configured | `Channel` and protocol-classified `Stream` entries | Source-loader, adapter, parser, transport, and XMLTV parser tests | Direct live URL resolution through the VLC desktop player | **Partially implemented** |
| M3U8/HLS | URI classification and manifest parser | HLS master/media manifest parser; no adaptive playback backend | `StreamURI`, `StreamManifest.HLS`, master variants, and media segments | Focused URI-classification and HLS parser tests | None | **Partially implemented** |
| Xtream Codes | Capability-oriented live, category-family, EPG, stream-resolution, VOD, and series provider adapter with secure credential retrieval | Encoded `player_api.php`, authentication response validation, live/VOD/series category and catalogue retrieval, short-EPG retrieval, factory registration, and validated live playback URL construction | Canonical `Category`, `Channel`, `EPGEntry`, `Movie`, and `Series` translation with local channel search; EPG is available to the safe Qt grid through registered-provider capability resolution | Focused request-builder, API-client, DTO translation, adapter, registration, resolver, and EPG grid tests | Direct live URL resolution through the VLC desktop player | **Partially implemented** |
| Stalker/MAG | Capability-oriented provider adapter with volatile session state | MAG/Stalker client adapter | `Channel`, `EPGEntry`, and resolved `URL`; EPG is available to the safe Qt grid through registered-provider capability resolution | Unit, integration, resolver, and EPG grid tests | Direct live URL resolution through the VLC desktop player | **Partially implemented** |
| Ministra | Separate device-facing provider required; administrative REST API is explicitly out of player scope | Compatibility assessment completed; implementation requires an authorized, sanitized portal fixture and approved device identity | Planned canonical translation boundary for portal DTOs; no runtime client claim | Assessment plus future fixture-backed contract tests required | None | **Assessed — implementation gated** |
| MPEG-DASH | URI classification and MPD parser | Bounded MPD parser for live/VOD type and representations; no adaptive playback backend | `StreamURI`, `StreamManifest.DASH`, and canonical MPD representations | Focused URI-classification and DASH parser tests | None | **Partially implemented** |
| RTMP | URI classification foundation | RTMP(S) transport detection | Protocol-classified `StreamURI` and `Stream` | Focused URI-classification tests | None | **Partially implemented** |

## Ordering rationale

The project will not start desktop UI work until the domain, application ports, provider adapters, and persistence/player composition have stable contracts. Phase 2 therefore focuses on deterministic parsing and domain behavior; it is the appropriate next increment after the core-recovery milestone.

Each phase must add or update focused tests and pass the full quality gate before it is marked complete.
