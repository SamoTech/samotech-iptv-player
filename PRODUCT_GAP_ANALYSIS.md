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
| Xtream live-TV component workflow | Authentication, catalogue, search, short EPG, and live stream resolution are implemented in the adapter; registered-playback use case and Qt channel browser exist. | Production composition now wires safe stores, services, use cases, theme, and one player; no executable lifecycle entry point exists yet. |
| MAG/Stalker live-TV component workflow | Authorized MAC identity, session lifecycle, live catalogue, search, EPG, and live link resolution exist behind the adapter. | Requires an authorized provider; production composition is present but the lifecycle/launcher remains incomplete. |
| M3U catalogue component workflow | Local/file/HTTP(S) source loading, extended-M3U parsing, source protection, live catalogue, and search are implemented. | The adapter does not yet provide registered playback resolution. |
| Local recording component workflow | Active libVLC playback can be duplicated to a safe timestamped local `.ts` file. | Requires active playback and lacks a recording-library experience. |
| Persisted settings component workflow | System/light/dark preference can be persisted, loaded by production composition before bootstrap, and presented in a Qt settings dialog. | An executable lifecycle still must launch the UI and close resources safely. |

## Partially usable capabilities

| Priority | Gap | Why it is partial | Recommended completion direction |
|---|---|---|---|
| **P0** | No runnable application lifecycle or entry point | Production composition now initializes repositories, restores metadata, creates provider services/context/use cases, loads theme, and shares one player. No lifecycle owner invokes it, runs qasync, reports generic startup failures, or closes resources. | Add a CLI/module entry point and graceful startup/shutdown lifecycle around the production root. |
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

The dependency-wiring portion of this gap is complete: `build_production_desktop_application()` now performs configuration, safe-store initialization, metadata restoration, provider-service/use-case construction, initial-theme loading, player construction, and Qt shell composition. The remaining P0 gap is lifecycle ownership and an executable entry point; the project cannot yet act as a complete IPTV desktop application because no supported path performs the final lifecycle steps:

```text
production composition root
  → invoke from an executable entry point
  → run qasync event loop
  → report only generic startup failures
  → close managed resources safely
```

This remains the correct current milestone because lifecycle ownership turns the delivered composition graph into a usable user workflow without changing provider protocols or adding product polish ahead of functionality.

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
| 1 | Production composition root | **Completed.** Existing services, repositories, provider registry/factory/context, use cases, theme, and one player are constructible/testable as one application graph, with safe metadata restoration. |
| 2 | Startup/shutdown lifecycle and entry point | A user can launch the desktop shell through supported code, receives generic startup failures, and managed state is closed safely. |
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
