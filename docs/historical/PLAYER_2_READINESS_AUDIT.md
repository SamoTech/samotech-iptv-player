# Player 2.0 Readiness Audit

**Repository:** SamoTech IPTV Player
**Audit date:** 2026-08-16
**Baseline:** Current `origin/main` fetched and verified before this audit.
**Status vocabulary:** `OBSERVED`, `TESTED`, `INFERRED`, `UNKNOWN`, `DEFERRED`, `NOT EXECUTED`, and `BLOCKED` are used deliberately.

This is the mandatory read-only readiness audit for the Player 2.0 commercial playback phase. No production implementation change was made before this report. The audit preserves the existing provider, qasync, PySide6, artwork, Favorites, History, `ResolvedPlayback`, generation/session, and shared libVLC boundaries.

## 1. Current Player Architecture

The current dependency direction is `provider adapter → translator → canonical domain → application use cases and ports → ResolvedPlayback → PlayerPort → libVLC → PySide6`. Xtream, MAG/Stalker, and M3U remain provider/source concerns. Provider adapters own credentials, volatile session state, provider-specific URL construction, and response translation. Presentation consumes canonical DTOs and application boundaries.

`desktop_composition.build_production_desktop_application()` constructs one shared `VlcPlayerAdapter`, one shared HTTP client, application use cases, provider services, SQLite repositories, keyring-backed credential storage, and `MainWindow`/`PlayerShell`. The Qt video surface owns the native window target; the player adapter owns libVLC playback and recording.

**Classification:** `OBSERVED`, `TESTED` through composition and integration coverage.

## 2. PlayerPort Capability Matrix

| Capability | Current contract | Evidence | Classification |
|---|---|---|---|
| Play | `async play(ResolvedPlayback)` | `PlayerPort`, adapter tests | TESTED / IMPLEMENTED |
| Pause | `async pause()` | `PlayerPort`, adapter/UI tests | TESTED / IMPLEMENTED |
| Resume | `async resume()` | `PlayerPort`, adapter/UI tests | TESTED / IMPLEMENTED |
| Stop | `async stop()` | `PlayerPort`, adapter/UI tests | TESTED / IMPLEMENTED |
| Restart | No typed method; can be represented as stop/play only through a higher service | Source audit | DEFERRED |
| Toggle play/pause | No PlayerPort method; PlayerShell infers from status text | PlayerShell source | PARTIAL / RISK |
| Current position | No property/method | PlayerPort source | NOT SUPPORTED |
| Duration | No property/method | PlayerPort source | NOT SUPPORTED |
| Percentage | No property/method | PlayerPort source | NOT SUPPORTED |
| Seek forward/backward/absolute | No method | PlayerPort source | NOT SUPPORTED |
| Volume/mute | No method/property | PlayerPort source | NOT SUPPORTED |
| Audio/subtitle tracks | No method/property | PlayerPort source | NOT SUPPORTED |
| Fullscreen | Window presentation behavior, not PlayerPort | PlayerShell source | TESTED presentation-only |
| Native video output | `attach_video_output(int)` | adapter and native surface tests | TESTED / IMPLEMENTED |
| Recording | Typed start/stop methods | adapter tests | TESTED / IMPLEMENTED |
| Boolean playing/recording | Properties | adapter tests | TESTED / LIMITED |
| Explicit state | Internal VLC state only; not exposed as typed application state | adapter source | PARTIAL |
| Metadata | Not exposed by PlayerPort | source audit | NOT SUPPORTED |
| Diagnostics | Structured logs exist in adapter; no typed diagnostic stream | adapter tests/log audit | PARTIAL |

No capability will be claimed or implemented merely because libVLC may expose a loosely typed method. Native availability and safe cross-platform semantics must be proven first.

## 3. VLC Adapter Capability Matrix

`VlcPlayerAdapter` creates or accepts one libVLC instance/player, subscribes to six lifecycle events when available, uses an asyncio lock for command serialization, constructs media only from `ResolvedPlayback`, supports typed transport metadata, network caching, one software fallback retry, native output attachment, recording through duplicate output, and explicit close/release.

The internal lifecycle currently includes `IDLE`, `STARTING`, `PLAYING`, `BUFFERING`, `RECOVERING`, `STOPPING`, `STOPPED`, and `FAILED`. It does not expose a public Player 2.0 state model. Native callbacks are reduced to labels, logged with media/session generations, and routed back to the owning event loop after the callback returns.

Live EOF/STOPPED recovery is bounded by existing attempt/window/backoff/stability controls. The adapter intentionally treats buffering as a watchdog input rather than immediate media reconstruction. The existing tests cover duplicate buffering, EOF, stop, recovery limits, stability reset, explicit-stop invalidation, channel switching, stale generations, and shutdown.

**Classification:** `OBSERVED`, `TESTED` synthetically; native Windows execution is `NOT EXECUTED` in the current Linux environment.

## 4. Current PlayerShell UI

The current PlayerShell presents a dominant video stage with a dark/blue overlay. The overlay contains playback context, status, Pause, Play/Resume, Stop, current-channel context, and a Fullscreen button. The overlay auto-hides after a timer and reappears on interaction. Fullscreen toggles the existing Qt window using `showFullScreen()`/`showNormal()`; it does not create a second window or player.

The shell exposes keyboard handling for supported shortcuts, selection/search/category controls, Movie/Series detail surfaces, artwork placeholders/loaders, Favorites actions, and generation-safe non-live navigation. It does not expose seek, elapsed/duration, volume/mute, audio track, subtitle track, aspect-ratio, or diagnostics settings controls.

`MainWindow` exposes generic Pause, Resume, Stop, Start Recording, and Stop Recording actions. Errors are generic and provider-safe. The current PlayerShell pause/play toggle infers state from status text rather than a typed player state.

**Classification:** `OBSERVED`, `TESTED` through offscreen/native PlayerShell probes and presentation tests.

## 5. Current Playback State Model

There are two separate current models. `PlayPlaybackTarget` exposes an attempt/result model with `PLAYED`, `STALE`, `UNSUPPORTED`, and `FAILED` outcomes. `VlcPlayerAdapter` maintains an internal lifecycle state for libVLC/recovery. PlayerShell maintains presentation fields such as selected, loading, playing, and playback-error channel identity.

There is no single application-owned explicit state machine covering `IDLE`, `LOADING`, `BUFFERING`, `PLAYING`, `PAUSED`, `STOPPING`, `STOPPED`, `ENDED`, `RECOVERING`, and `ERROR`. This is the primary Player 2.0 architecture gap and must be addressed before commercial controls depend on state.

**Classification:** `OBSERVED`; explicit public state model is `DEFERRED` pending Phase 1 design.

## 6. Current Event Model

libVLC event callbacks attach to Opening, Buffering, Playing, EncounteredError, EndReached, and Stopped where the binding exposes them. Callback code logs aggregate safe correlation data and uses `call_soon_threadsafe()` to schedule asynchronous handling. The adapter does not perform blocking media work in the callback thread.

Duplicate events are guarded by session/media generations, active recovery task checks, intentional-action flags, and the play lock. EncounteredError is subscribed and logged but does not currently expose a typed application state transition. `PLAYING`, `BUFFERING`, `END`, and `STOPPED` are the primary state/recovery inputs exercised by current tests.

**Classification:** `OBSERVED`, `TESTED` synthetically; native event completeness is `UNKNOWN` outside the Windows probe.

## 7. Current Generation/Session Model

`VlcPlayerAdapter` tracks media generation, session token, event sequence, intentional actions, recovery tasks, watchdog/stability tasks, and closed state. `PlaybackAttemptRegistry` invalidates previous application playback attempts before resolution and checks staleness before player mutation, after player play, and before history recording.

PlayerShell separately tracks request, non-live, and artwork generations. Provider selection cancels owned tasks, invalidates pending playback, clears artwork/provider state, and prevents stale completions from mutating the new provider context. Closing the shell marks it disposed and cancels owned tasks.

**Classification:** `OBSERVED`, `TESTED` by stale-result, rapid-selection, provider-switch, artwork, concurrency, and native probes.

## 8. Current Live EOF Recovery Interaction

Live EOF and unexpected STOPPED events can schedule bounded recovery after generation/session validation. A watchdog can classify prolonged STARTING/BUFFERING as a recovery input. Recovery uses the existing media reconstruction path, exponential backoff, attempt limit, time window, and stability reset.

Explicit stop, shutdown, channel switch, pause, recording restart, and provider/playback invalidation cancel or invalidate recovery. The current tests verify duplicate events do not create duplicate recovery, transient buffering does not immediately restart, and stale EOF cannot restart new media.

**DO NOT CHANGE boundary:** preserve the five-attempt limit, 45-second window, backoff, stability guard, generation/session guards, and explicit-stop invalidation unless a blocking Player 2.0 defect is demonstrated with a regression test.

**Classification:** `OBSERVED`, `TESTED`; preserved and out of scope for unproven redesign.

## 9. Current VOD Playback Flow

Xtream Movie selection resolves through the existing `PlaybackTarget.movie`/provider non-live resolver path. The provider adapter validates provider-scoped IDs, builds an opaque stream descriptor, resolves the authorized URL into `ResolvedPlayback`, and `PlayPlaybackTarget` calls `PlayerPort.play()`. History is recorded after successful player start using the current minimal History contract.

Movie containers are playable; Series containers are not. No UI constructs Xtream URLs or accesses credentials. Real populated-provider Movie playback remains outside current evidence.

**Classification:** `OBSERVED`, `TESTED` synthetically; real provider playback `NOT EXECUTED`/`BLOCKED` by evidence.

## 10. Current Series/Episode Playback Flow

Series is a browsable container. PlayerShell navigates Series → Season → Episode through application discovery use cases with non-live generation guards. Episode selection creates an episode-specific `PlaybackTarget`, resolves through the provider-neutral resolver, and reaches `ResolvedPlayback`/`PlayerPort` in the same way as Movie playback.

The existing Episode DTO contains duration/plot metadata where provider payloads supply it, but there is no episode-specific resume/completion capability. Real populated-provider Episode playback is not executed.

**Classification:** `OBSERVED`, `TESTED` synthetically/native; populated provider `NOT EXECUTED`.

## 11. Current History Model

History is an immutable record with `id`, `item_id`, `item_type`, `watched_at`, `duration_seconds`, and `position_seconds`. SQLite persists records by record ID and orders recent entries by timestamp. `RecordHistory` creates a new record after playback start, defaulting duration and position to zero.

There is no provider identity, started/updated timestamp pair, completion flag, watched percentage, durable content key, or update-in-place progress operation. The existing library UI can display stored values but does not offer true replay/resume.

**Classification:** `OBSERVED`, `TESTED`; playback-start history is implemented, resume is not.

## 12. Current Resume Limitations

The current PlayerPort has no position, duration, seek, or completion methods. The current History record cannot distinguish unknown duration from zero, cannot identify provider scope safely, and is created at playback start. Therefore true VOD resume, episode-specific resume, completion tracking, and watched percentage cannot be implemented honestly without typed contract and migration work.

The Player 2.0 phase must not display fake resume or infer completion from a start record. If native evidence supports position/duration, the safe path is to extend typed contracts and storage deliberately, with backward-compatible migration and provider-scoped content identity. Live resume must remain opt-in and must not inherit VOD semantics automatically.

**Classification:** `OBSERVED`, `DEFERRED` pending typed design and native evidence.

## 13. Current Audio/Subtitle Limitations

PlayerPort exposes no audio or subtitle enumeration/selection/disable API. The VLC adapter’s fake/player protocol likewise has no typed track methods. The presentation layer exposes no track menus. libVLC/python-vlc capability availability and cross-platform behavior have not yet been proven in this repository.

No fake track list will be created. Track support is `NOT SUPPORTED` today and must remain `UNKNOWN` until native probing proves a safe abstraction.

## 14. Current Volume/Mute Limitations

PlayerPort exposes no volume, mute, unmute, or toggle-mute method/property. PlayerShell and MainWindow do not provide volume controls. This capability is `NOT SUPPORTED` by the current typed boundary and cannot be claimed from libVLC assumptions alone.

## 15. Current Fullscreen Behavior

Fullscreen is implemented as presentation/window behavior on the existing Qt window. It uses the same video surface, player, and libVLC instance. The overlay reappears after the toggle and the button text changes between Fullscreen and Exit fullscreen. Escape/window handling is part of the existing event-filter path and must be re-tested if controls are expanded.

**Classification:** `TESTED` presentation behavior; true native fullscreen/player-output acceptance on Windows is `NOT EXECUTED`.

## 16. Current Seek Limitations

There is no seek bar, elapsed time, duration display, ±10/±30-second control, or absolute seek method. The current adapter does not query or set media position/time. Seek is `NOT SUPPORTED` and must not be faked through UI state.

## 17. Current Duration/Position Limitations

Duration exists only as optional provider metadata in Movie/Episode DTOs and as a request field in History; it is not current media duration. There is no runtime media position or duration observation at PlayerPort or adapter level. Any future duration/position feature must distinguish provider metadata from native playback measurements.

## 18. Current Concurrency Model

Application playback attempts are serialized by the attempt registry and checked around resolve/play/history boundaries. VLC commands are serialized by an asyncio lock. Recovery, watchdog, and stability tasks are owned by the adapter and cancelled on explicit lifecycle changes. PlayerShell asynchronous operations use qasync-owned tasks and generation guards.

The model is designed for A→B, A→B→C, Live↔Movie, Series→Episode, provider switching, close/shutdown, stale callback, stale artwork, and recovery invalidation safety. Existing deterministic concurrency coverage is strong, but new state/control tasks must integrate with the same ownership and generation scheme.

## 19. Current qasync Ownership

`create_owned_task()` associates presentation awaitables with an owner, cancels them on close/destruction, consumes task failures, and allows global shutdown cancellation. PlayerShell uses this for provider refresh, catalogue operations, playback actions, artwork, and dialogs. The adapter routes native callbacks back to the event loop and uses `asyncio.to_thread()` for blocking libVLC method calls.

No new polling loop, background thread, duplicate player, or duplicate HTTP session is justified by the audit.

## 20. Current Shutdown Behavior

PlayerShell marks itself disposed, stops overlay timers, invalidates non-live requests, and cancels owned tasks. Production runtime closes the shared HTTP client after the qasync loop exits. The VLC adapter’s `close()` is idempotent, invalidates recovery, stops playback, releases player and instance, and suppresses non-fatal shutdown cleanup failures.

Native Windows lifecycle evidence is available only through the provider-free WAV probe, which reports `SKIP reason=windows_required` on Linux and must not be called a Windows pass here.

## 21. Existing Tests

The repository contains focused coverage for VLC controls, retries, recording, event subscriptions, diagnostics redaction, live EOF/STOPPED recovery, buffering watchdog behavior, stability windows, attempt limits, explicit-stop/shutdown invalidation, stale generations, transport metadata, PlayerPort handoff, playback controls, PlayerShell navigation/overlay/keyboard/stale protections, Xtream Movie/Series/Episode flows, artwork, Favorites, History, MAG, M3U, and provider boundaries.

The existing quality baseline has passed full offscreen pytest with 8,417 statements and 74% coverage, Ruff, Black, mypy, `git diff --check`, native PlayerShell, concurrency, and performance probes. Those are inherited evidence and will be re-run after each Player 2.0 increment.

## 22. Existing Native Probes

`tests/player_shell_native_probe.py` exercises offscreen Qt PlayerShell behavior, including stale provider/content/playback safety, overlay/accessibility, local search/filter, artwork, and navigation. `tests/player_shell_performance_probe.py` measures catalogue/content behavior through 10K/50K/100K checkpoints. `tests/vlc_native_lifecycle_probe.py` is Windows-only and uses a local silent WAV, no provider URL, and aggregate event labels to validate binding, creation, playback, replacement, stop, and cleanup.

Native track/position/volume probes do not yet exist. They must be added only if the current platform and binding expose safe capabilities.

## 23. KiddaC Technology Comparison

EStalker and XStreamity were reviewed as technology references only. Their repositories visibly contain separate live/VOD/series/player/resume/settings/server/task modules and expose practical concepts such as media lifecycle separation, playlist/category navigation, replay/resume persistence, and settings-driven player behavior. These observations are references, not evidence that SamoTech should copy their APIs or Enigma2 architecture.

SamoTech’s safe adaptation boundary remains typed provider/application ports, canonical DTOs, PySide6, qasync, SQLite/keyring, provider-scoped identity, `ResolvedPlayback`, and one libVLC player. No Enigma2 UI, global playlist state, service references, decoder internals, provider-specific legacy URL construction, credentials handling, or source code is to be copied. References: [EStalker](https://github.com/kiddac/EStalker/tree/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker) and [XStreamity](https://github.com/kiddac/XStreamity/tree/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity).

## 24. Risks

The primary risks are: extending PlayerPort without proving libVLC/python-vlc support on Linux and Windows; making runtime callbacks mutate UI state from native threads; conflating provider metadata duration with media runtime duration; corrupting or overclaiming History/resume; modifying Live EOF recovery while adding generic state handling; creating duplicate player/output paths; adding polling timers that degrade UI responsiveness; exposing raw provider diagnostics; and claiming Windows or populated-provider acceptance without execution.

## 25. Recommended Implementation Order

The implementation order is: design typed PlayerPort capabilities; define a public explicit state machine; add adapter state/event mapping with generation/session guards; add position/duration/seek only where native evidence supports them; add volume/mute; investigate tracks and add only supported typed abstractions; design provider-scoped History/resume/completion migration; integrate PlayerShell state; add commercial controls and fullscreen overlay; improve safe error/recovery UX; expand concurrency tests; run native probes; measure performance; perform security audit; update documentation; run final gates; then commit/push/final audit.

At each step, a capability that is not supported by the binding or contract remains explicitly deferred rather than simulated.

## 26. Explicit DO NOT CHANGE Boundaries

The following boundaries are frozen unless a blocking defect is proven with evidence and a migration plan: provider architecture and authentication; MAG implementation; Xtream implementation; M3U implementation; Live playback; bounded Live EOF recovery and its five-attempt/45-second/backoff/stale-guard policy; shared libVLC ownership; qasync/task ownership; `PlayerShell` composition boundaries; `ResolvedPlayback`; provider-scoped identity; artwork security/cache limits; Favorites; and existing generation/session protections.

Do not add provider URL construction to UI, direct libVLC imports to presentation, fake resume, fake tracks, raw URL/secret diagnostics, a second player, a second HTTP session, uncontrolled global cache, or undocumented provider behavior.

## Audit Conclusion

The repository has a solid player foundation but not a commercial Player 2.0 capability surface. The highest-value safe work is an explicit public playback state model integrated with existing adapter event/generation semantics, followed by only the native capabilities that can be proven. True resume, seek, tracks, and volume/mute are contract changes rather than cosmetic UI tasks. The next phase may begin only now that this audit is complete.

## References

1. [SamoTech README](README.md)
2. [SamoTech architecture](../../ARCHITECTURE.md)
3. [SamoTech project status](../../PROJECT_STATUS.md)
4. [SamoTech product gap analysis](PRODUCT_GAP_ANALYSIS.md)
5. [EStalker](https://github.com/kiddac/EStalker/tree/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker)
6. [XStreamity](https://github.com/kiddac/XStreamity/tree/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity)
