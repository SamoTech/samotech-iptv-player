# Wave 3 Playback Lifecycle and Product-Surface Audit

## 1. Lifecycle Ownership

The current implementation already serializes play, stop, restart, pause, resume, recording restarts, and recovery through one `VlcPlayerAdapter` lock and one media-generation/session-token model. A Wave 3 `PlaybackSession` replacement is therefore not introduced: the existing adapter plus `PlaybackStateMachine` is the only lifecycle owner. This prevents UI controls, provider refreshes, and native callbacks from creating concurrent media sessions.

## 2. Buffering, Liveness, and Recovery

| Requirement | Current evidence | Wave 3 disposition |
|---|---|---|
| Loading/playing/buffering state | Native-event mapping plus public typed state | Implemented at deterministic boundary |
| Buffering does not restart immediately | Buffering watchdog only requests bounded recovery after threshold | Preserved |
| Live stall detection | Generation/session-scoped media-time heartbeat for typed LIVE resources | Implemented and deterministic-tested |
| Live END/STOPPED/error recovery | Existing bounded retry/window/backoff policy | Preserved; no second system added |
| VOD/episode natural completion | Typed non-live END reaches `ENDED` without live rebuild | Implemented and deterministic-tested |
| Provider-specific expiry/session cause | libVLC does not expose provider HTTP/token cause | Blocked without authorized provider trace |

No cache tuning, reconnect option, decoder override, or provider-specific retry was changed because current evidence does not identify any of those as the cause of a real Wave 3 failure.

## 3. Channel Switching

The adapter stops/releases prior media before a new resolved playback opens, increments media generation, invalidates stale recovery work, and ignores callbacks whose generation/session token is obsolete. This is the correct current seam for switch-race protection. The Phase 27 large-data probe additionally measured row selection and scroll at catalogue scale; it did not pretend to prove remote provider switching latency.

## 4. VOD and Series

Movie and episode playback are already separate provider-capability paths. The application exposes duration/seek/progress/resume only for non-live content and keeps VOD/episode END out of live recovery. Existing provider contracts support Xtream movie/series metadata, season/episode discovery, and resolved-playback handoff. No universal provider capability claim is added for M3U or MAG VOD/series/catch-up.

## 5. EPG and Catch-up

EPG parsing, canonical entries, and presentation are present at deterministic boundaries for existing provider families. Catch-up remains intentionally unavailable: a capability enum value or legacy internal method is not evidence of a provider-neutral archive URL contract or executable playback. Wave 3 therefore leaves catch-up disabled/unsupported rather than adding an unusable control.

## 6. Player UI and Diagnostics

The PlayerShell already gates controls by typed player capabilities, exposes native audio/subtitle selection, local subtitle attachment, subtitle delay, aspect ratio, seek/resume for non-live content, volume/mute, recording, and fullscreen. Diagnostics record safe player/session/recovery state but do not currently prove container classification, codec selection, decoded video frames, or audio initialization. The controlled public HLS probe also could not reach libVLC initialization in this Linux sandbox.

The product/diagnostic conclusion is consequently: **do not expose codec, audio, HLS, or runtime claims beyond the existing evidence matrix.**

## References

[1]: `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` — lifecycle/recovery and native control implementation.  
[2]: `src/samotech_iptv/application/player_state_machine.py` — typed playback-state contract.  
[3]: `src/samotech_iptv/presentation/player_shell.py` — capability-gated player controls.  
[4]: `docs/evidence/WAVE3_CAPABILITY_MATRIX.md` and `docs/evidence/WAVE3_RUNTIME_PROBE_LOG.md` — runtime evidence boundaries.
