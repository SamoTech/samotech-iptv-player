# Roadmap

## Current project status

The repository scaffold and the core recovery are complete. The recovered core is installable, has a single configuration boundary, uses domain-oriented provider ports, includes a tested MAG/Stalker adapter, and passes the configured test, type, and lint checks.

> **Current phase:** Phase 2 — Domain completion and M3U parsing — **completed**.
> **Completed milestone:** Core recovery, MAG provider integration, an initial domain-oriented M3U parser, validated catalogue, user-library, Stream, programme-record, and value-object contracts, with focused tests.
> **Next product milestone:** Provider-management design and a future M3U provider adapter; this integration is deliberately deferred from Phase 2.

| Phase | Scope | Status |
|---:|---|---|
| **Recovery** | Packaging repair; configuration composition; canonical provider ports; MAG adapter/credential/session ownership; integration coverage; strict quality gate; truthful documentation | **Completed** |
| **1** | Repository scaffold, baseline architecture, CI configuration, module placeholders | **Completed** |
| **2** | Complete domain entities and value objects; M3U parser; parser and domain unit tests | **Completed** — extended-M3U parser plus focused validation coverage for all current domain records and value objects are delivered; M3U provider-adapter integration is deferred to provider-management work |
| **3** | VLC/player adapter, SQLite repositories, dependency-injection composition root, and basic window | Planned |
| **4** | Channel browser UI, search, favorites, and watch history | Planned |
| **5** | Xtream Codes and Stalker provider clients; playlist manager UI | Partially advanced by the recovered MAG/Stalker core and explicit capability declarations; M3U, Xtream, Ministra, and player integration remain planned |
| **6** | XMLTV EPG parser and EPG grid view | Planned |
| **7** | Stream recording through the player adapter and recording UI | Planned |
| **8** | Plugin SDK, example provider plugin, and plugin loader | Planned |
| **9** | Theme engine, dark/light styles, and settings UI | Planned |
| **10** | Auto-updater, crash reporting, picture-in-picture, subtitle/audio management | Planned |
| **11** | Performance pass, memory profiling, and large-playlist stress testing | Planned |
| **12** | PyInstaller packaging, Windows installer, and release automation | Planned |

## Provider and protocol support matrix

> **Status convention:** An integration is marked **Implemented** only where executable processing through its stated layer and focused tests exist. **Partially implemented** records a functioning subset; **Planned** indicates that no executable support claim is made.

| Integration | Architecture | Parser/API | Domain translation | Tests | Player backend | Status |
|---|---|---|---|---|---|---|
| M3U playlist | Capability-oriented provider adapter | Local-file and HTTP(S) source loader plus extended-M3U parser | `Channel` and protocol-classified `Stream` entries | Source-loader, adapter, parser, and transport tests | None | **Partially implemented** |
| M3U8/HLS | URI classification and manifest parser | HLS master/media manifest parser; no adaptive playback backend | `StreamURI`, `StreamManifest.HLS`, master variants, and media segments | Focused URI-classification and HLS parser tests | None | **Partially implemented** |
| Xtream Codes | Capability-oriented live, VOD, and series provider adapter with secure credential retrieval | Encoded `player_api.php`, authentication response validation, live/VOD/series DTO retrieval, and factory registration | Canonical `Channel`, `Movie`, and `Series` translation with local channel search | Focused request-builder, API-client, DTO translation, adapter, and registration tests | None | **Partially implemented** |
| Stalker/MAG | Capability-oriented provider adapter with volatile session state | MAG/Stalker client adapter | `Channel`, `EPGEntry`, and resolved `URL` | Unit and integration tests | None | **Partially implemented** |
| Ministra | Platform-specific compatibility assessment pending | No Ministra client | None | None | None | Planned |
| MPEG-DASH | URI classification and MPD parser | Bounded MPD parser for live/VOD type and representations; no adaptive playback backend | `StreamURI`, `StreamManifest.DASH`, and canonical MPD representations | Focused URI-classification and DASH parser tests | None | **Partially implemented** |
| RTMP | URI classification foundation | RTMP(S) transport detection | Protocol-classified `StreamURI` and `Stream` | Focused URI-classification tests | None | **Partially implemented** |

## Ordering rationale

The project will not start desktop UI work until the domain, application ports, provider adapters, and persistence/player composition have stable contracts. Phase 2 therefore focuses on deterministic parsing and domain behavior; it is the appropriate next increment after the core-recovery milestone.

Each phase must add or update focused tests and pass the full quality gate before it is marked complete.
