# VLC IPTV Playback Remediation Audit

**Repository:** [SamoTech/samotech-iptv-player](https://github.com/SamoTech/samotech-iptv-player)
**Scope:** Windows + PySide6 + python-vlc/libVLC IPTV playback reliability remediation
**Author:** Manus AI
**Date:** 2026-08-18

> **Final decision:** The observed media-level stall gap is **FIXED at the typed libVLC boundary** and is covered by deterministic tests and the successful hosted Windows artifact workflow. The result is **PARTIAL / READY FOR CONTROLLED AUTHORIZED PROVIDER VALIDATION**, not a universal or commercial-compatibility claim, because populated real-provider playback continuity, provider-specific media headers, temporary URL refresh, and MAG media watchdog requirements remain unproven.

## 1. Baseline commit

The inherited Phase 0 baseline was repository commit `1f3e8b2`, with a clean worktree and **94 focused provider/player/application tests passing** before the new remediation work. The historical v0.1.4 release tag remains unchanged. The remediation was implemented and committed as `04a9d1b` (`feat: add live stream stall detection heartbeat`) and pushed normally to `origin/main`; no force push, history rewrite, release-tag modification, or README badge-block edit occurred.

The baseline specification identified v0.1.4 startup as healthy: the process, Qt GUI, libVLC runtime, and initial playback all started. The remediation therefore deliberately stayed inside media playback lifecycle handling rather than changing startup, PySide6, packaging, or the media backend.

## 2. Exact code audit findings

The original player already owned one libVLC instance, one media player, media generations, session tokens, event subscriptions, buffering state, recovery tasks, a buffering watchdog, stability tracking, bounded retries, backoff, software fallback, and secret-safe diagnostics. That architecture was preserved.

The proven defect was that `MediaPlayerPlaying` changed the adapter to `PLAYING`, but no task verified that media time advanced. The existing watchdog started only after a `BUFFERING` callback. A remote stream could therefore stop delivering usable media while VLC continued reporting a healthy-looking playing/process state and while no buffering/error/end event arrived. A second classification defect was that all current-generation `END_REACHED` events entered the live recovery path even when the resource was a movie or episode.

| Finding | Classification | Evidence |
|---|---|---|
| Startup/runtime failure caused the observed stop | **PROVEN false for this incident** | v0.1.4 startup, GUI, libVLC loading, and initial playback were already passing |
| No media-level progress/liveness check | **PROVEN gap; FIXED** | Source audit of `VlcPlayerAdapter` before commit `04a9d1b` |
| Buffering watchdog covered every stall | **PROVEN false** | Watchdog was event-driven and only started from `BUFFERING` |
| `END_REACHED` was differentiated by typed content | **PROVEN false; FIXED** | Prior handler routed current-generation END directly to live recovery |
| Existing bounded recovery architecture was reusable | **PROVEN** | Recovery task, attempt budget, window, backoff, stale-generation checks, and intentional-action checks already existed |
| M3U User-Agent/Referer metadata was lost | **FIXED in prior work** | Parser → `TransportMetadata` → libVLC option tests |
| Xtream or MAG media-plane headers were proven necessary | **NOT PROVEN** | No authorized media-plane evidence in the repository |

## 3. IPTVnator findings applied

The remediation applied only architecture-level patterns from [IPTVnator](https://github.com/4gray/iptvnator): separate stable content identity from temporary transport URLs; preserve provider/content context to the playback boundary; protect asynchronous work with current generation/session checks; emit structured, redacted playback diagnostics; and use evidence-driven, bounded recovery rather than unconditional restart.

`PlaybackResource` remains the stable logical identity. `ResolvedPlayback.url` and `TransportMetadata` remain ephemeral. The liveness task carries the media generation and session token captured at native `PLAYING`, and every recovery request is routed through the existing task, retry budget, window, and backoff. IPTVnator’s Angular, TypeScript, browser playback, hls.js, Video.js, Shaka, Electron, and engine-specific implementations were not copied.

## 4. KiddaC findings applied

The public [KiddaC EStalker](https://github.com/kiddac/EStalker) and [XStreamity](https://github.com/kiddac/XStreamity) references were used only for Stalker/MAG control-plane concepts: profile selection, handshake/token lifecycle, cookies, selected request headers, `create_link`, portal session behavior, and the distinction between provider failure/recovery patterns.

The values `1`, `4097`, `5001`, `5002`, and `8193` remain correctly excluded from the VLC implementation. They are Enigma2 service/player selectors, not VLC protocols or libVLC options. No Enigma2 player, service type, or alternate media backend was added.

## 5. Changes to VlcPlayerAdapter

The adapter now accepts `live_stall_timeout_s`, defaulting to **15 seconds**, and validates it with the existing non-negative recovery duration checks. It owns `_liveness_task`, `_last_media_position_ms`, and `_last_position_advance_at`. The liveness task is started only when the current typed `PlaybackResource.content_type` is `LIVE` and the adapter enters internal `PLAYING`.

The task samples the existing `_VlcPlayer.get_time()` method through `asyncio.to_thread()`. A valid forward position update resets the progress deadline and emits a safe `MEDIA_PROGRESS` diagnostic. An unchanged position beyond the threshold invokes `_request_recovery("STALLED", generation, session_token)`. No public `STALLED` state was added and no `is_playing()` polling was used as the health signal.

The task is cancelled through the existing lifecycle invalidation path on stop, pause, channel switch, recovery, recording restart, and shutdown. It is also cancelled whenever the adapter leaves `PLAYING`. The adapter’s single recovery task remains the only recovery architecture.

The event handler now uses typed resource context. LIVE `END_REACHED` remains recovery-eligible as `EOF`; MOVIE and EPISODE END reach the existing public `ENDED` state without rebuilding media. Typed non-live STOPPED reaches `STOPPED`, and typed non-live ENCOUNTERED_ERROR reaches the existing `ERROR` state without entering live recovery.

## 6. Transport metadata changes

No speculative provider metadata was added in this remediation. The already-implemented provider-neutral `TransportMetadata` boundary remains ephemeral, secret-safe, and validated. Explicit `TransportHeader` values, User-Agent, and Referer reach libVLC through `:http-header`, `:http-user-agent`, and `:http-referrer` options. Header names reject line breaks and duplicate case-insensitive names; header values reject line breaks.

Generated credential-bearing options are not logged. The adapter logs only safe provider/content labels, media type, transport type, generation, event sequence, state reason, retry information, and error classification. Xtream and MAG control-plane headers/cookies are not forwarded to the media plane without authorized evidence.

## 7. M3U changes

The prior M3U remediation remains in force. `M3USourceLoader` reads bounded UTF-8 local content and canonicalizes CRLF and CR to LF, which makes Windows local playlist loading platform-independent without altering the parser contract. Remote playlist content remains bounded and uses the existing HTTP client path.

The M3U parser maps supported `http-user-agent`/`user-agent` and `http-referrer`/`referrer` aliases into `TransportMetadata`. The provider adapter returns the resolved URL plus metadata to the shared player. M3U cookie and arbitrary-header inference remains unimplemented without evidence; this is intentional rather than an omission disguised as support.

## 8. Xtream changes

No provider architecture rewrite or speculative refresh mechanism was added. `XtreamRequestBuilder` continues to construct URL-shaped live, movie, and series paths using the provider credential boundary. `XtreamProviderAdapter` continues to return URL-based `ResolvedPlayback` values, while `PlayPlaybackTarget` attaches the stable provider-scoped `PlaybackResource` for live, movie, and episode playback.

This preserves logical identity across temporary URL values, but the current provider contract does not retain a playback-session refresh callback or prove URL expiry behavior. Expired temporary URL recovery and refresh races remain **REQUIRES AUTHORIZED PROVIDER VALIDATION** rather than blindly retrying the same URL.

## 9. MAG changes

No MAG watchdog endpoint was invented. The existing MAG implementation remains profile-driven, with handshake, token/session state, selected control-plane headers/cookies, bounded GET retry, refresh, and `create_link` handling. The application boundary continues to narrow executable playback handoff to the supported HTTP(S) URL value object.

The media-plane requirement for a portal watchdog/event request is not established by repository fixtures or an authorized provider trace. It is therefore classified **REQUIRES AUTHORIZED PROVIDER VALIDATION**. Control-plane MAC, token, cookie, Authorization, and portal headers remain outside `ResolvedPlayback.transport` unless future provider evidence proves a specific media-plane requirement.

## 10. Buffering changes

The default `network_caching_ms=1000`, live buffering timeout of 10 seconds, recovery window of 45 seconds, recovery backoff of 1 to 8 seconds, and stability interval of 5 seconds were not increased speculatively. Separate live/VOD cache policies were not introduced because no controlled measurement established cache size as the incident cause.

The existing buffering watchdog still waits through transient buffering and recovers only after its configured timeout. The new heartbeat complements, rather than replaces, it: a stream that remains in `PLAYING` without advancing media time is now eligible for bounded `STALLED` recovery even if VLC never emits a fresh `BUFFERING` event.

## 11. Recovery changes

Recovery remains generation/session scoped and bounded. Every attempt uses the current `ResolvedPlayback`, current transport metadata, current provider/content context, retry budget, recovery window, and exponential delay. Duplicate pending recovery is ignored. Intentional stop, pause, shutdown, channel switch, stale callbacks, attempt exhaustion, and window exhaustion do not create infinite recovery loops.

The only new recovery reason is `STALLED`, routed through `_request_recovery()` and `_recover_after_delay()`. `ENCOUNTERED_ERROR` continues to use the existing bounded live recovery policy. LIVE EOF and unexpected LIVE STOPPED remain recovery-eligible. VOD/EPISODE EOF is completion, and typed non-live STOPPED/ERROR are not live interruptions.

## 12. Media liveness changes

The liveness heartbeat is intentionally media-level rather than process-level. It does not equate a responsive GUI, a live Python process, or `is_playing()` with usable media. It observes the existing libVLC media clock through `get_time()` and treats only forward time movement as progress.

The sampling interval is bounded to at most two seconds and approximately one-third of the configured stall threshold, with a small lower bound for deterministic operation. The default policy therefore allows normal short buffering and scheduling variance while bounding indefinite silent stalls. A valid negative/unavailable media-time sample is ignored rather than treated as a false stall.

The heartbeat is enabled only when typed resource context proves `ContentType.LIVE`. Legacy URL-only callers preserve existing live recovery compatibility but do not receive typed liveness classification. This avoids inferring media type from URL text.

## 13. Tests

The focused VLC adapter suite passed **48 tests** after the final event-classification additions. It includes live stall detection, position-advancement reset, liveness cancellation on stop and channel switch, typed MOVIE/EPISODE normal completion, typed non-live STOPPED/ERROR behavior, live EOF recovery, encountered-error recovery, stale generation protection, intentional-stop protection, buffering timeout, bounded retry/backoff, media-option generation, and secret-safe diagnostics.

The focused provider/application/security selection passed **66 tests**. The complete non-presentation corpus passed after the remediation changes; the final collected scope is **885 tests**. Coverage XML was generated in the local run. The test suite continues to exclude presentation tests in the Linux sandbox because Qt presentation collection is an existing environment limitation.

## 14. Synthetic matrix

The detailed deterministic matrix is recorded in [`build/PHASE7_SYNTHETIC_PLAYBACK_MATRIX.md`](build/PHASE7_SYNTHETIC_PLAYBACK_MATRIX.md). It classifies M3U HTTP/HLS and metadata paths, Xtream live/VOD/episode URL boundaries, MAG control-plane and `create_link` boundaries, live progress/stall/buffering/error/EOF/STOP behavior, VOD/episode completion, stale generation, retry budget, and secret-safe diagnostics.

The matrix distinguishes synthetic boundary proof from populated provider behavior. Xtream expiry/refresh races, MAG authenticated media continuity, MAG stream interruption coupled to portal session expiry, and provider-specific media headers remain explicitly unproven.

## 15. Windows validation

The exact pushed commit `04a9d1b` passed the official [Windows Portable EXE workflow run 32159903781](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32159903781) on the hosted Windows runner. The following gates passed: dependency installation, pinned VLC acquisition and runtime validation, Ruff, Black, MyPy, the Windows non-Qt test corpus, native VLC lifecycle validation, one-file PyInstaller EXE creation, packaged-VLC smoke, Qt/application smoke with startup diagnostics, normal and sanitized PATH validation outside the repository, artifact-content audit, SHA256 generation, build metadata, and portable artifact upload.

The workflow’s tagged-release publishing job was skipped because this push was to `main` and did not create or modify a release tag. This is **NOT REACHED**, not a failure. The separate CI run `32159904001` and CodeQL run `32159903767` also completed successfully for the same commit.

The official workflow proves application startup, GUI/VLC runtime loading, packaging, path handling, and deterministic native lifecycle behavior. It does **not** itself open a commercial IPTV URL and measure multi-minute media continuity, because no provider credentials or real stream fixture are injected into the workflow. Therefore Windows media continuity and recovery against a populated provider remain **NOT TESTED**.

## 16. Real-provider validation

No populated Xtream or MAG media session was executed as part of this remediation commit. The repository contains no committed credentials, and the hosted Windows workflow does not receive real-provider secrets. Real-provider validation must be performed separately with authorized, sanitized fixtures and redacted telemetry.

The real-provider classification is **REQUIRES AUTHORIZED PROVIDER VALIDATION** for Xtream temporary URL expiry/refresh behavior, provider-specific media headers/cookies, MAG portal media lifetime, and any MAG watchdog/event endpoint. This is an explicit limitation, not evidence that those features are required or absent for every provider.

## 17. Security validation

The focused sensitive-logging suite passed. The changed source and test diff contains no authorized Xtream credential values, MAG MAC, token, cookie, Authorization value, or credential-bearing URL. Existing diagnostics continue to use redacted URLs and bounded labels. CodeQL run `32159903767` completed successfully for commit `04a9d1b`.

Ruff, Black, MyPy, Bandit, and `git diff --check` passed locally. `pip-audit` remains **PARTIAL / PRE-EXISTING ENVIRONMENTAL BLOCKER** because the sandbox reports four known vulnerabilities in packages outside this remediation scope: `pypdf 6.14.2`, `wheel 0.42.0`, and `xhtml2pdf 0.2.14`, plus the local project distribution not being available on PyPI. No speculative dependency upgrade was made.

## 18. Documentation changes

`docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` now describes the implemented typed LIVE heartbeat, `get_time()` position evidence, `STALLED` routing through existing bounded recovery, typed LIVE versus MOVIE/EPISODE END semantics, and the remaining provider-specific limitations. The phase ledgers [`build/PHASE4_PIPELINE_AUDIT.md`](build/PHASE4_PIPELINE_AUDIT.md), [`build/PHASE7_SYNTHETIC_PLAYBACK_MATRIX.md`](build/PHASE7_SYNTHETIC_PLAYBACK_MATRIX.md), and [`build/PHASE8_GATE_CLASSIFICATION.md`](build/PHASE8_GATE_CLASSIFICATION.md) preserve the inspection, matrix, and gate evidence.

The README badge block was not touched. No release version metadata, provider architecture, UI, PyInstaller workflow, or unrelated documentation was changed by this remediation commit.

## 19. Unresolved issues

| Issue | Classification | Required next evidence |
|---|---|---|
| Populated real IPTV stream remains continuously playable after recovery | **NOT TESTED** | Authorized Windows provider session with redacted lifecycle telemetry |
| Xtream temporary URL expiry and refresh race | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Provider contract or sanitized expiry/refresh trace |
| Xtream provider-specific media headers/cookies | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Authorized media request evidence |
| MAG media watchdog/event endpoint | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Authorized portal profile trace proving endpoint and lifecycle |
| MAG media-plane headers/cookies required by resolved stream | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Authorized captured media request requirements |
| Separate live/VOD cache profile | **NOT TESTED / NOT JUSTIFIED** | Controlled measurements showing 1000 ms cache is causal |
| RTSP/RTMP/UDP/RTP/SRT executable provider-to-player support | **PARTIAL** | Explicit supported transport contract and Windows/libVLC acceptance |
| Pre-existing pip-audit findings | **PARTIAL / ENVIRONMENTAL BLOCKER** | Dependency-maintenance decision outside this remediation |

## 20. Final readiness classification

The final classification is **PARTIAL — MEDIA-STALL REMEDIATION FIXED AT THE TESTED TYPED LIBVLC BOUNDARY; CONTROLLED AUTHORIZED PROVIDER VALIDATION REQUIRED**.

The required lifecycle is now represented in the preserved architecture as:

```text
RESOLVE
  → OPEN
  → PLAY
  → CONTINUE PLAYING [get_time() advances]
  → DETECT STALL [position unchanged beyond bounded threshold]
  → RECOVER WHEN APPROPRIATE [existing bounded recovery]
  → FAIL CLEANLY WHEN NOT RECOVERABLE [existing retry/window/error states]
```

This is stronger than a GUI, process, DLL, or startup pass: the adapter now has deterministic evidence for media progress and a bounded action when live progress stops. It is not a claim that every provider’s session, headers, URL lifetime, codec, or stream format is compatible. The remediation is ready for an authorized Windows real-provider continuity run, but should not be classified as universally or commercially validated until that run demonstrates sustained media playback and recovery against the affected provider.

## References

[1]: https://github.com/4gray/iptvnator "IPTVnator repository"
[2]: https://github.com/kiddac/EStalker "KiddaC EStalker repository"
[3]: https://github.com/kiddac/XStreamity "KiddaC XStreamity repository"
[4]: https://wiki.videolan.org/VLC_command-line_help/ "VideoLAN VLC command-line help"
[5]: https://images.videolan.org/vlc/features.html "VideoLAN VLC features"
[6]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "SamoTech VlcPlayerAdapter"
