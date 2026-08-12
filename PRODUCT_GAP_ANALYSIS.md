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
| Xtream live-TV component workflow | Authentication, catalogue, search, short EPG, and live stream resolution are implemented in the adapter; registered-playback use case and Qt channel browser exist. | Production composition and the source-install lifecycle wire safe stores, services, use cases, theme, and one player; VOD/series UI workflows remain incomplete. |
| MAG/Stalker live-TV component workflow | Authorized MAC identity, session lifecycle, live catalogue, search, EPG, and live link resolution exist behind the adapter. | Requires an authorized provider; source-install lifecycle is present, but only the live-TV subset is implemented. |
| M3U live-TV component workflow | Local/file/HTTP(S) source loading, extended-M3U parsing, source protection, live catalogue/search, and parsed HTTP(S) resolution through the registered-player path are implemented. | Non-HTTP(S) transports are classified but remain outside the current player URL boundary; XMLTV and non-live workflows are incomplete. |
| Local recording component workflow | Active libVLC playback can be duplicated to a safe timestamped local `.ts` file. | Requires active playback and lacks a recording-library experience. |
| Persisted settings component workflow | System/light/dark preference can be persisted, loaded by production composition before bootstrap, and presented in a Qt settings dialog. | A source-install lifecycle launches the UI and closes the shared HTTP resource; applying a newly saved preference immediately remains optional work. |

## Partially usable capabilities

| Priority | Gap | Why it is partial | Recommended completion direction |
|---|---|---|---|
| **P0** | Registered catalogue discovery is incomplete | Xtream adapter category/movie/series capabilities and canonical records exist, but no registered-provider resolver/use-case/desktop catalogue flow exposes them safely. | Add one capability-bounded browse-only catalogue workflow with adapter, application, and Qt tests; do not claim playback until stream resolution is proven. |
| **P1** | Detailed player-state and active-item UX is absent | The desktop menu now has generic pause/resume/stop actions, but `PlayerPort` does not expose a full paused/stopped state model or active-item context. | Add state/capability contracts only when they are proven necessary by a bounded workflow; do not inspect libVLC from the UI. |
| **P1** | EPG source integration is incomplete | MAG/Xtream EPG and safe grid work; XMLTV parsing has explicit mapping but no provider source binding, fetch, persistence, or refresh. | Define XMLTV source/mapping lifecycle and expose it only after bounded integration tests. |
| **P1** | Favorites and history lack complete user workflows | Persistence/use cases exist, and a selected channel can be favorited, but no library pages/removal/history/resume UX exists. | Add safe list/remove/history views and separate progress/resume policy. |
| **P2** | Xtream VOD/series do not reach application/UI workflows | Adapter methods and canonical domain records exist, but no resolver ports/use cases/UI navigate categories, movies, series, or episodes. | Add capability-specific resolver/use cases and first browse-only UI; only then add playback where provider contracts are verified. |
| **P2** | MAG non-live content is absent | No canonical MAG VOD, series, category, or archive execution path is implemented. | Deliver only against authorized fixtures, one capability at a time. |
| **P2** | Runtime media capability negotiation is absent | Stream transport/manifest types are classified, but the application cannot state whether the actual libVLC runtime supports a resolved stream or selected tracks. | Add player capability/state contracts once the runnable lifecycle is stable. |
| **P2** | Recording library management is absent | Recording can start/stop but there is no metadata index, list, retention policy, or safe user destination preference. | Add local recording metadata and UI after core playback lifecycle. |

## Missing core functionality

### Completed — Runnable Desktop Composition and Provider Lifecycle

The dependency-wiring and source-install lifecycle work are complete. `build_production_desktop_application()` performs configuration, safe-store initialization, metadata restoration, provider-service/use-case construction, initial-theme loading, player construction, and Qt shell composition. `samotech-iptv` and `python -m samotech_iptv` invoke that root, run qasync, return generic startup failures, and close the shared HTTP resource after the window loop exits.

Packaging, installers, update delivery, crash-reporting policy, and broader operational diagnostics remain separate production-hardening work; they do not block source-install launch.

### Completed — M3U registered stream resolution

M3U now completes the same registered HTTP(S) playback flow as Xtream/MAG. The adapter advertises `LIVE`, `SEARCH`, and `STREAM_RESOLUTION`; it parses the current playlist, matches the canonical channel, converts only supported HTTP(S) stream URIs into the existing player `URL` contract, and returns generic failures for unknown channels or unsupported transports. The resolver-to-player integration is covered without exposing playlist or stream secrets.

### Completed — Generic desktop playback controls

The Qt Playback menu now invokes dedicated pause, resume, and stop application use cases against the existing `PlayerPort` and shared libVLC adapter. Success and failure feedback is intentionally generic, so presentation status never carries stream URLs, credentials, or provider secrets. The current port exposes `is_playing` but no complete paused/stopped state model; the UI deliberately does not infer state from libVLC internals.

### Completed — Safe provider lifecycle management

Registered providers can now be edited and removed through type-aware Qt dialogs. Edits expose only non-secret base/source metadata and blank credential-replacement inputs; blank optional credential fields retain existing OS-keyring values. Removal deletes persisted non-secret metadata, deletes the associated OS-keyring entry when present, and deregisters the runtime profile. Application and presentation failures remain generic, and focused lifecycle tests prove credential preservation, cleanup, metadata deletion, and registry synchronization.

### P0 — Registered catalogue discovery

The next capability must extend discovery rather than bypass the clean architecture. Xtream exposes adapter-level category, movie, and series methods, but these do not yet have registered-provider resolver ports, application use cases, or desktop browsing. Deliver one browse-only capability at a time through the provider factory/resolution boundary, with authorized fixtures and no premature VOD/series playback claim.

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
| 2 | Startup/shutdown lifecycle and entry point | **Completed.** A user can launch the desktop shell through supported code, receives generic startup failures, and the shared HTTP resource is closed safely. |
| 3 | M3U playback resolution | **Completed.** The M3U source type completes the registered HTTP(S) live-TV playback path with safe failure boundaries. |
| 4 | Playback controls and safe status | **Completed.** Pause, resume, and stop actions delegate through `PlayerPort` with generic Qt feedback and one shared libVLC player. |
| 5 | Provider lifecycle management | **Completed.** Type-aware edit/removal safely preserves blank credential fields, cleans keyring entries, updates metadata, and synchronizes the registry. |
| 6 | Registered catalogue discovery | **Current P0.** Add bounded browse-only category, movie, or series discovery where adapter contracts and fixtures prove the capability. |
| 7 | EPG/library completion | Users can configure guide sources and maintain personal state safely. |
| 8 | VOD/series playback, protocol breadth, and hardening | Higher-breadth capabilities build on a viable product lifecycle. |

## Non-negotiable constraints for future work

- Keep libVLC as the sole player backend and PySide6/Qt as the sole desktop toolkit unless an explicit product decision changes that policy.
- Do not put credentials, MAC addresses, tokens, or resolved stream URLs in logs, presentation status text, persistent provider metadata, test fixtures, or documentation examples.
- Do not infer Ministra compatibility from MAG/Stalker; follow the dedicated assessment gate.
- Do not claim HLS/DASH, catch-up, VOD, series, favorites, history, or transport playback is complete unless a tested end-to-end path exists.
- Continue the direct-to-`main` workflow with the required full quality gate before every commit.
