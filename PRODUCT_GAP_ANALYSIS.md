# Product Gap Analysis

> **Current-state authority:** [PROJECT_STATUS.md](PROJECT_STATUS.md) is the repository’s source of truth for implemented, partially implemented, and planned capability claims. This document prioritizes the distance between those capabilities and a usable, reliable IPTV desktop product.

## Assessment principle

The highest priority is assigned to work that lets an authorized user complete an essential workflow safely. A product foundation, parser, adapter, or UI dialog does not eliminate a gap until the relevant end-to-end path is composed, launchable, observable, and recoverable. Polish, telemetry, and distribution improvements should not displace a missing core workflow.

| Priority | Meaning |
|---|---|
| **P0 — Product blocker** | Prevents the application from being used as its stated product. |
| **P1 — Core feature** | Completes a primary user workflow after the product blocker is addressed. |
| **P2 — Important enhancement** | Meaningfully improves usability, breadth, reliability, or maintainability but is not required for the first viable workflow. |
| **P3 — Future** | Valuable but dependent on earlier decisions, provider evidence, platform support, or product validation. |

## Already usable as components

The repository has a tested Clean Architecture foundation and executable pieces of a live-TV desktop workflow. Provider adapters can translate supported provider data into canonical records; application use cases can browse channels, resolve supported streams, and invoke the libVLC player port; the Qt layer provides secure provider-entry, listing, live-channel browsing/search, EPG display, recording controls, and theme settings. SQLite and keyring adapters preserve the intended split between non-secret state and secrets.

| Capability | Evidence of usability today | Boundaries |
|---|---|---|
| Xtream live-TV component workflow | Authentication, catalogue, search, short EPG, and live stream resolution are implemented in the adapter; registered-playback use case and Qt channel browser exist. | Requires manual construction of dependencies because no production composition root/launcher exists. |
| MAG/Stalker live-TV component workflow | Authorized MAC identity, session lifecycle, live catalogue, search, EPG, and live link resolution exist behind the adapter. | Requires an authorized provider and manual composition; only the live-TV subset is implemented. |
| M3U catalogue component workflow | Local/file/HTTP(S) source loading, extended-M3U parsing, source protection, live catalogue, and search are implemented. | The adapter does not yet provide registered playback resolution. |
| Local recording component workflow | Active libVLC playback can be duplicated to a safe timestamped local `.ts` file. | Requires active playback and lacks a recording-library experience. |
| Persisted settings component workflow | System/light/dark preference can be persisted and presented in a Qt settings dialog. | A production root must load the preference and launch the UI lifecycle. |

## Partially usable capabilities

| Priority | Gap | Why it is partial | Recommended completion direction |
|---|---|---|---|
| **P0** | No runnable application composition and lifecycle | Existing bootstrap/runtime boundaries require callers to provide fully constructed use cases and a preloaded theme. No entry point initializes repositories, restores metadata, creates provider services/context, or closes resources. | Build a production composition root, then a CLI/module entry point and graceful lifecycle. |
| **P0** | M3U cannot resolve a parsed stream through the registered-player path | M3U exposes live catalogue/search but not `PlaybackProvider`; parsed streams are not retained or resolved by the adapter. | Add safe parsed-channel/stream lookup and `PlaybackProvider` implementation, then test registered M3U playback orchestration. |
| **P1** | Provider management ends at add/list | Registration and metadata persistence exist, but users cannot edit/remove profiles or observe lifecycle errors safely. | Add delete/update contracts, credential cleanup, registry refresh, safe dialog actions, and tests. |
| **P1** | Playback UX lacks state and direct controls | The player adapter supports play/pause/resume/stop, but the desktop menu currently exposes recording controls only. | Add generic playback state/status and pause/resume/stop actions without revealing stream URLs. |
| **P1** | EPG source integration is incomplete | MAG/Xtream EPG and safe grid work; XMLTV parsing has explicit mapping but no provider source binding, fetch, persistence, or refresh. | Define XMLTV source/mapping lifecycle and expose it only after bounded integration tests. |
| **P1** | Favorites and history lack complete user workflows | Persistence/use cases exist, and a selected channel can be favorited, but no library pages/removal/history/resume UX exists. | Add safe list/remove/history views and separate progress/resume policy. |
| **P2** | Xtream VOD/series do not reach application/UI workflows | Adapter methods and canonical domain records exist, but no resolver ports/use cases/UI navigate categories, movies, series, or episodes. | Add capability-specific resolver/use cases and first browse-only UI; only then add playback where provider contracts are verified. |
| **P2** | MAG non-live content is absent | No canonical MAG VOD, series, category, or archive execution path is implemented. | Deliver only against authorized fixtures, one capability at a time. |
| **P2** | Runtime media capability negotiation is absent | Stream transport/manifest types are classified, but the application cannot state whether the actual libVLC runtime supports a resolved stream or selected tracks. | Add player capability/state contracts once the runnable lifecycle is stable. |
| **P2** | Recording library management is absent | Recording can start/stop but there is no metadata index, list, retention policy, or safe user destination preference. | Add local recording metadata and UI after core playback lifecycle. |

## Missing core functionality

### P0 — Runnable Desktop Composition and Provider Lifecycle

The primary gap is a missing production composition root. The project cannot yet act as a complete IPTV desktop application because it has no supported path that performs the following coherent lifecycle:

```text
configuration
  → initialize SQLite repositories
  → restore safe provider metadata to registry
  → construct keyring/provider factory/context/services/use cases
  → load persisted theme
  → build desktop application
  → run qasync event loop
  → close managed resources safely
```

This is the correct current milestone because it turns already tested abstractions into a usable user workflow without changing provider protocols or adding product polish ahead of functionality.

### P0 — M3U registered stream resolution

M3U is a first-class source type in registration and browsing, but it cannot complete the same registered playback flow as Xtream/MAG because the M3U adapter advertises `LIVE` and `SEARCH`, not `STREAM_RESOLUTION`. This makes it a P0 follow-on after lifecycle composition: it closes a core provider-to-player gap using data the parser already produces.

### P1 — Complete live-TV interaction

A viable live-TV player needs pause/resume/stop, safe load/play error presentation, active-item context, and a coherent provider lifecycle. Those controls should be implemented against the existing `PlayerPort` and libVLC only. The work must not introduce another player backend.

### P1 — Complete EPG and personal library workflows

Guide parsing, favorites, and history exist as component foundations. A usable player needs a reliable path to configure/update guide sources and navigate, remove, and resume personal library state without leaking provider secrets.

## Production hardening

| Priority | Gap | Why it is deferred from the first runnable milestone |
|---|---|---|
| **P2** | Packaging and release automation | The CI configuration has a best-effort Windows PyInstaller build, but no stable product entry point/lifecycle exists to package. |
| **P2** | Large-playlist performance and memory profiling | Must measure the composition/lifecycle and real catalog flows first. |
| **P2** | User-safe diagnostics and recoverable startup errors | Requires a central lifecycle boundary to own failure handling and reporting. |
| **P3** | Crash reporting | Requires explicit privacy, consent, provider, retention, and redaction decisions. |
| **P3** | Auto-updating | Requires target platforms, package/distribution channel, manifests, signing, rollback, and support policy. |
| **P3** | Plugin signing/sandboxing/marketplace | The current plugin SDK intentionally supports trusted local code only; a broader model needs a separate security/product decision. |

## Future features

| Priority | Opportunity | Dependency or decision gate |
|---|---|---|
| **P2** | Xtream movie/series/episode browsing and playback | Capability-specific application/UI work and verified VOD/episode resolution behavior. |
| **P2** | Subtitle/audio track selection and aspect/fullscreen controls | libVLC state/capability contract and desktop playback UX. |
| **P3** | Picture-in-picture | Platform support, window behavior, and control/interaction requirements. |
| **P3** | Ministra adapter | Authorized sanitized portal fixture and approved device identity; a separate device-facing protocol implementation. |
| **P3** | Catch-up/archive | Provider-specific authorized fixtures and explicit product behavior. |
| **P3** | Remote provider/plugin discovery | Security model and user-consent changes; current trusted-local plugin policy intentionally excludes it. |

## Recommended execution sequence

| Sequence | Bounded increment | Outcome |
|---:|---|---|
| 1 | Production composition root | Existing services, repositories, provider registry/factory/context, use cases, and theme become constructible/testable as one application graph. |
| 2 | Startup/shutdown lifecycle and entry point | A user can launch the desktop shell through supported code and state is initialized/restored safely. |
| 3 | M3U playback resolution | The M3U source type can complete the registered live-TV playback path. |
| 4 | Playback controls and safe status | The live-TV workflow becomes operable rather than merely invocable by double-click. |
| 5 | Provider lifecycle and EPG/library completion | Users can maintain sources and personal state safely. |
| 6 | VOD/series, protocol breadth, and hardening | Higher-breadth capabilities build on a viable product lifecycle. |

## Non-negotiable constraints for future work

- Keep libVLC as the sole player backend and PySide6/Qt as the sole desktop toolkit unless an explicit product decision changes that policy.
- Do not put credentials, MAC addresses, tokens, or resolved stream URLs in logs, presentation status text, persistent provider metadata, test fixtures, or documentation examples.
- Do not infer Ministra compatibility from MAG/Stalker; follow the dedicated assessment gate.
- Do not claim HLS/DASH, catch-up, VOD, series, favorites, history, or transport playback is complete unless a tested end-to-end path exists.
- Continue the direct-to-`main` workflow with the required full quality gate before every commit.
