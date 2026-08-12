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

## Current milestone — Runnable Desktop Composition and Provider Lifecycle

The current project milestone is **Runnable Desktop Composition and Provider Lifecycle**.

### Objective

Make the existing, tested provider → application → libVLC → Qt capabilities available as a coherent application lifecycle. This milestone must construct dependencies safely, initialize and restore non-secret state, load the persisted theme, launch the desktop runtime, and close resources predictably.

### Why this is next

The repository already contains individual provider adapters, secure registration services, SQLite repositories, use cases, a Qt bootstrap factory, and a qasync runtime. However, no production composition root or executable entry point constructs and connects them. The current bootstrap accepts already-constructed use cases and the runtime is referenced only in focused tests. Therefore a user cannot yet launch the complete registered-provider live-TV workflow from the repository as a supported application.

This product blocker has higher value and lower dependency risk than auto-updating, crash reporting, picture-in-picture, or cosmetic work. Those capabilities should build on a stable application lifecycle rather than precede it.

### Bounded delivery increments

| Increment | Scope | Exit criteria |
|---|---|---|
| 1. Composition root | Construct existing configuration, storage, keyring, provider factory/registry/context, registration/catalogue/resolution services, use cases, player, and theme; restore persisted safe metadata. | A fake-backed integration test verifies construction and metadata restoration without accessing real providers or secrets. |
| 2. Startup and shutdown lifecycle | Initialize repositories, load the initial theme, run the qasync desktop loop, and close lifecycle-managed resources safely. | Focused lifecycle tests cover success and generic startup failure paths. |
| 3. CLI entry point | Add a documented module or console entry point that invokes the production lifecycle. | A smoke test verifies safe argument handling and composition delegation. |
| 4. Provider management completion | Add user-facing provider removal/edit behavior and predictable persisted-registry refresh. | Provider metadata and credential cleanup are tested, with no secret leakage. |

## Next milestone — Usable live-TV workflow completion

After the application can be launched, the next product milestone should complete the live-TV workflow rather than start broad VOD or polish work.

| Priority | Candidate | Rationale |
|---|---|---|
| P0 | M3U registered-stream resolution | The M3U adapter currently exposes catalogue/search but not the playback capability required by the registered-player path. Completing it enables a primary provider type to play its parsed live streams. |
| P1 | Playback-state, failure, and stop controls | A user needs clear generic status feedback and direct playback controls around the active libVLC session. |
| P1 | Provider lifecycle management UI | Users need to remove or update registered sources and understand inactive/invalid profiles without exposing secrets. |
| P1 | EPG-source binding | XMLTV parser capability must be connected to provider/source configuration before it becomes a user-facing guide source. |

## Future milestones

The items below should be sequenced only after the product-blocking lifecycle and usable live-TV workflow have progressed.

| Milestone | Scope | Dependency notes |
|---|---|---|
| Catalogue expansion | Xtream VOD/movie/series/episode browsing and playback; provider-specific category navigation. | Requires registered-provider resolver/use-case/UI extensions and player behavior for non-live content. |
| MAG/Stalker expansion | Category, VOD, series, archive/catch-up capabilities where authorized fixtures prove behavior. | Requires protocol-specific evidence and capability-by-capability delivery. |
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
