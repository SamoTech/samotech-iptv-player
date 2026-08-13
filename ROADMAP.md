# Product Roadmap

## Roadmap authority

This document explains **delivery direction**. The verified current-state capability matrices, quality baseline, known limitations, and last verified commit live in [PROJECT_STATUS.md](PROJECT_STATUS.md). Historical commit and phase records remain useful evidence, but they are not current-state authority.

## Product direction

SamoTech IPTV Player is being built as an **extensible, provider-agnostic IPTV desktop player and media-platform foundation**. Its progression is organized by product and architectural dependencies rather than by a sequence of opaque phase numbers.

```text
Foundation
    ↓
Canonical domain and provider abstraction
    ↓
Provider/protocol integration
    ↓
Stream resolution and playback engine
    ↓
Desktop experience
    ↓
Runnable application lifecycle
    ↓
Catalogue completion and production hardening
```

## Completed milestones

The following work is present in the repository and has focused test coverage. “Completed” records delivered boundaries and does not imply that every feature is available from a packaged end-user launcher.

| Product milestone | Historical work mapped to it | Delivered result |
|---|---|---|
| Foundation and recovery | Initial scaffold; Phase 1; Clean Architecture Phase A/B; packaging and CI recovery | Python package structure, strict tooling, core/domain/application/infrastructure/presentation boundaries, configuration, test foundation, and direct-to-main recovery workflow. |
| Canonical IPTV domain | Historical Phase 2 and subsequent domain increments | Validated canonical channels, streams, categories, providers, movies, series, episodes, EPG, favorites, history, credentials, URLs, capabilities, stream transports, and themes. |
| Provider abstraction | Architecture refinement; provider ports/capabilities; factory/registry/context work | Capability-oriented provider interfaces, provider factory, registry, secure registration, metadata persistence, resolution services, and credential boundaries. |
| M3U source foundation | M3U parser and adapter increments | Extended-M3U parsing, safe local/file/HTTP(S) source loading, protected tokenized sources, canonical live channels, and local search. |
| HLS/DASH/XMLTV foundations | Manifest and XMLTV parser increments | Bounded HLS and MPD metadata parsers, transport/manifest classification, and bounded secure XMLTV parsing with explicit mappings. |
| MAG/Stalker live-TV foundation | MAG provider recovery and adapter work | Authorized MAC handling, private session state, live catalogue, local search, EPG, stream resolution, and session refresh through the canonical adapter boundary. |
| MAG/Stalker compatibility lab | Protocol profile and local fixture increment | Legacy and opt-in Stalker-query handshake profiles, bounded discovery, deterministic response/error and resource-lifecycle fixtures, controlled session re-authentication tests, redacted protocol diagnostics, and documented firmware/middleware evidence boundaries. Production portal compatibility remains unresolved until an authorized portal trace proves a profile. |
| Xtream Codes foundation | Xtream request/client/translator/adapter increments | Authentication, live channels, category families, movie/series catalogues, short EPG, local search, and live stream resolution. |
| Playback engine | libVLC adapter, composition, and recording work | Sole libVLC player backend with play/pause/resume/stop, Qt output attachment, and local MPEG transport-stream recording. |
| Desktop foundation | PySide6, qasync, provider-entry, browser, EPG, and library increments | Qt video surface, main window, provider registration/listing, live-channel browser/search/playback action, EPG grid, favorites insertion, history recording, and recording controls. |
| Theme and settings | Historical Phase 9 | Persisted system/light/dark preference, deterministic Qt styling, startup theme parameter, Settings menu, and settings dialog. |
| Trusted local plugin SDK | Provider-plugin increment | Explicit trusted-local plugin loading, API/identity/namespace validation, transactional registration, failure isolation, and reference plugin. |

## Historical phase reconciliation

Historical phase labels are preserved for traceability. The labels below are mapped to their actual outcome so that phase numbering does not obscure the product state.

| Historical phase or report | Actual outcome | Current interpretation |
|---|---|---|
| Recovery / Phase 1 | Scaffold, CI, architecture baseline, later recovery work | Completed foundation, with some early documents superseded by current status. |
| Phase 2 | Domain/value-object coverage and M3U parser | Completed canonical-model and parser foundation. |
| Phase 3 | Player adapter, SQLite repositories, basic Qt composition | Completed component-level playback and persistence foundation. |
| Phase 4 | Channel browser, search, favorites, history | Completed partial desktop/library experience; favorites/history management remains incomplete. |
| Phase 5 | Xtream and Stalker provider work | Completed partial provider foundation; provider-specific VOD/series/catch-up product workflows remain incomplete. |
| Phase 6 | XMLTV and EPG grid | Completed parser/grid foundation; XMLTV source binding remains incomplete. |
| Phase 7 | libVLC recording and UI controls | Completed active-stream recording foundation. |
| Phase 8 | Trusted local provider plugin SDK | Completed constrained extensibility feature. |
| Phase 9 | Theme engine and settings UI | Completed persisted settings/theme foundation. |

## Completed milestone — Runnable Desktop Composition and Provider Lifecycle

This milestone is **completed** for source installs. The project now constructs, launches, and closes the supported desktop application lifecycle without exposing provider secrets in startup feedback.

### Objective

Make the existing, tested provider → application → libVLC → Qt capabilities available as a coherent application lifecycle. This milestone must construct dependencies safely, initialize and restore non-secret state, load the persisted theme, launch the desktop runtime, and close resources predictably.

### Why this is next

The repository now has a production composition root and supported source-install lifecycle. `samotech-iptv` and `python -m samotech_iptv` invoke composition, run qasync, provide generic startup failure feedback, and close the shared HTTP resource after the window loop exits. This makes the existing registered-provider desktop workflow launchable from a source installation.

This product blocker has higher value and lower dependency risk than auto-updating, crash reporting, picture-in-picture, or cosmetic work. Those capabilities should build on a stable application lifecycle rather than precede it.

### Bounded delivery increments

| Increment | Scope | Exit criteria |
|---|---|---|
| 1. Composition root | **Completed.** `build_production_desktop_application()` constructs configuration, SQLite repositories, keyring/context/registry/factory/services, use cases, one player, and the initial theme; it restores safe metadata. | Fake-backed integration coverage verifies construction, metadata restoration, M3U/Xtream/MAG factory registration, persisted-theme loading, and shared-player wiring without accessing real providers or secrets. |
| 2. Startup, shutdown, and CLI lifecycle | **Completed.** `samotech-iptv` and `python -m samotech_iptv` invoke composition, run qasync, return generic startup failure feedback, and close the shared HTTP resource. | Focused lifecycle and entry-point tests cover success, generic startup failure, composition delegation, and safe close behavior. |
| 3. Desktop playback controls | **Completed.** The Qt Playback menu invokes pause, resume, and stop application use cases against the one shared libVLC player and shows only generic success/failure text. | Focused application, presentation, bootstrap, and composition tests verify delegation, safe feedback, signal wiring, and shared-player construction. |
| 4. Provider management completion | **Completed.** User-facing type-aware provider edit/removal behavior now refreshes persisted metadata and the runtime registry. Blank optional credential inputs retain current keyring values; removal cleans the associated keyring entry. | Focused lifecycle, metadata, presentation, bootstrap, and composition coverage verifies credential preservation, cleanup, generic feedback, and production wiring. |
| 5. Registered live-category discovery | **Completed.** Registered Xtream live categories resolve through the registry, factory, typed category capability, canonical translation, browse use case, and a minimal Qt dialog. | Unit, resolver, provider, deterministic registry-to-adapter integration, presentation, bootstrap, and composition coverage verify safe browse-only behavior with no player path. |

## Current milestone — Usable live-TV workflow completion

The application can now launch from source. The next product milestone completes the primary live-TV workflow rather than starting broad VOD or cosmetic work.

| Priority | Candidate | Rationale |
|---|---|---|
| Completed | M3U registered-stream resolution | The M3U adapter now exposes `PlaybackProvider`, resolves parsed HTTP(S) streams from the current playlist, advertises `STREAM_RESOLUTION`, and completes the registered-player path with generic safe failures for unsupported boundaries. |
| Completed | Playback controls and safe status | The Qt Playback menu provides generic pause, resume, and stop actions through `PlayerPort` and the shared libVLC instance; detailed state is not inferred because the current port has no full paused/stopped state model. |
| Completed | Provider lifecycle management UI | Type-aware edit/removal dialogs preserve blank credentials, update safe metadata through the secure boundary, clean keyring entries on deletion, refresh the list, and keep the registry synchronized. |
| Completed | Registered live-category discovery | Registered Xtream live categories now use the typed category capability through the existing provider registry/factory path and render in a browse-only Qt dialog; they do not select content, resolve a stream, or play media. |
| Completed | Local XMLTV source binding and manual refresh | Registered providers can save a local path or local `file:` XMLTV source with explicit mappings, refresh it manually through the bounded parser, and view safe title/time rows. Remote/tokenized sources, cached guide persistence, and scheduled refresh are intentionally excluded. |
| P1 | User-library views | Existing favorites/history persistence and use cases need safe list, removal, and history views before resume behavior or non-live playback work. |

## Completed milestone — Favorites and History library views (2026-08-13)

Favorites now provides safe listing, empty state, refresh, generic errors, and single-record removal. History now provides recent listing, duration, persisted playback-position display, recency, refresh, generic errors, and confirmation-protected clear-all. History per-record deletion, replay, resume, provider reconstruction, and stream reconstruction remain out of scope.

## Current acceptance gate — live-provider runtime validation

The deterministic MAG compatibility lab and its failure-path resource cleanup are **implemented and tested**. The user has separately observed real Windows/libVLC playback for M3U and Xtream. Passing a fixture still does not establish production MAG portal support.

| Provider path | Current state | Required next evidence |
|---|---|---|
| M3U → channels → stream resolution → VLC | User-reported real Windows playback observed; this MAG increment made no M3U change. | Re-run only if a reproducible M3U regression is reported. |
| Xtream → channels → stream resolution → VLC | User-reported real Windows playback observed; this MAG increment made no Xtream change. | Re-run only if a reproducible Xtream regression is reported. |
| MAG → authentication → channels → stream resolution → VLC | Failure-safe discovery/session resource lifecycle is tested; the supplied real portal remains unresolved at authentication. | Authorized portal protocol trace or documented client contract that identifies a response-verified profile, then current-build Windows validation. |

## Future milestones

The items below should be sequenced only after the product-blocking lifecycle and usable live-TV workflow have progressed.

| Milestone | Scope | Dependency notes |
|---|---|---|
| Catalogue expansion | Xtream VOD/movie/series/episode browsing and playback; provider-specific category navigation. | Requires registered-provider resolver/use-case/UI extensions and player behavior for non-live content. |
| MAG/Stalker expansion | Category, VOD, series, archive/catch-up capabilities where authorized fixtures prove behavior. | Requires protocol-specific evidence and capability-by-capability delivery; current MAG category browsing is typed unsupported. |
| Ministra adapter | Separate device-facing Ministra integration. | Gated on authorized sanitized fixtures and approved device identity; see [MINISTRA_COMPATIBILITY_ASSESSMENT.md](MINISTRA_COMPATIBILITY_ASSESSMENT.md). |
| Library completion | Favorites and history lists, removal, resume behavior, and recording metadata management. | Builds on stable IDs, player-state events, and runnable lifecycle. |
| Playback experience | Subtitle/audio-track controls, aspect ratio/fullscreen, picture-in-picture, player capability negotiation, and transport diagnostics. | Must remain libVLC-only unless the product makes an explicit backend decision. |
| Production hardening | Packaging, installer/release process, crash reporting/privacy policy, update channel/signing, diagnostics, performance profiling, large-playlist testing, and recovery behavior. | Requires stable lifecycle and platform/distribution decisions. |

## Explicitly deferred items

- **Auto-updater and crash reporting** are not the immediate next phase. They require platform, distribution, privacy, data-retention, consent, and signing decisions.
- **Ministra support** is not inferred from the MAG/Stalker adapter; it requires its own authorized device-facing fixture and implementation.
- **Catch-up/archive support** is not implied by the capability enum or EPG parser.
- **HLS and MPEG-DASH adaptive playback** are not implemented by the Python parsers; stream decoding remains libVLC’s responsibility.
- **Plugin sandboxing, signing, automatic discovery, remote installation, and updates** are deliberately excluded from Plugin SDK API version 1.

## Development policy

The active branch is permanently `main`. The project workflow is:

```text
Inspect → Implement → Test → Quality gate → Commit → Push origin/main → Verify remote → Continue
```

No pull requests and no feature branches are used unless explicitly requested. Every commit must pass:

```bash
black --check src tests
ruff check src tests
mypy src
pytest -q
git diff --check
```

The current implementation status is authoritative in [PROJECT_STATUS.md](PROJECT_STATUS.md), while [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md) explains priorities and remaining work.


## MAG client-fingerprint compatibility increment

The bounded `stalker_client_compatibility` profile is **IMPLEMENTED and TESTED against local fixtures**. It remains a scoped live-TV protocol increment: strict token validation, private request fingerprint/cookies, live genre and ordered-list support, and command-based stream-link construction. The next acceptance boundary is not another profile: the authorized Windows portal must return a real JSON token, after which live records, stream resolution, and VLC audio/video can be verified in order. Until then, production MAG compatibility remains **UNRESOLVED**.
