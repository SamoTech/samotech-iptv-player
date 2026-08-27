# PHASE26_REAL_PLAYBACK_ACCEPTANCE_HARNESS

## 1. Baseline

Phase 26 began from the synchronized Phase 24 repository state at commit `31fdd28db21409a88c457e4b6a26a5a3ce384acc`, with a clean worktree and `HEAD == origin/main`. Application version `0.1.5`, the existing `v0.1.4` and `v0.1.5` tags/releases, release assets, CI workflows, and README badges were preserved.

The baseline evidence already classified real provider validation as **C — PROVIDER VALIDATION BLOCKED**. Phase 26 does not reopen that classification by inference. Its purpose is to make future authorized validation repeatable.

## 2. Harness Architecture

The harness is a separate tool at `tools/phase26_real_playback_harness.py`; it is not part of production startup or the production playback architecture. It has two explicit modes:

| Mode | Purpose | External provider claim |
|---|---|---|
| `mock` | Local-only generated M3U, mock Xtream, mock MAG/Stalker, deterministic media-time, stall, interruption, and switching scenarios | None; synthetic only |
| `real` | Accept one explicitly configured authorized stream through environment variables, instantiate the existing `VlcPlayerAdapter`, attach the existing `VlcVideoSurface`, and sample the application player port | PASS only with repeated real media-time progression |

The real path reuses `ResolvedPlayback`, `PlaybackResource`, `VlcPlayerAdapter`, `VlcVideoSurface`, and the existing player position/duration/state APIs. No second player, second recovery controller, alternate backend, provider rewrite, or UI change was introduced.

The mock server binds only to `127.0.0.1` on an ephemeral port. It exposes generated M3U, Xtream-like, and MAG/Stalker-like response shapes solely for deterministic harness testing.

## 3. Security Boundary

The harness accepts real configuration only through environment variables such as `PHASE26_STREAM_URL`, `PHASE26_PROVIDER_TYPE`, `PHASE26_CONTENT_TYPE`, and sampling parameters. No credentials are committed. The tool never prints or persists passwords, tokens, cookies, authorization headers, credential-bearing URLs, or raw configured stream URLs.

Evidence stores only a short SHA-256 stream identifier. Public demo fixtures are recorded by identifier and source, not as production configuration. Local mock response markers are synthetic session markers, not credentials.

Repository scans passed for the authorized credentials previously supplied during the task and for prohibited Enigma2 service selectors. The production code remains credential-safe.

## 4. M3U Validation

The harness generates a deterministic M3U playlist containing `tvg-id`, `tvg-name`, `group-title`, `tvg-logo`, and local synthetic stream paths. The local mock M3U endpoint serves the same content over loopback. The focused harness tests verified metadata presence, parser-compatible formatting, absence of credential markers, and local endpoint behavior.

Safe public HLS test sources were also inspected. The `video-commander/public-test-streams` repository identifies itself as a public test-media collection and is MIT licensed [1]. Mux’s HLS test page explicitly describes its streams as test HLS streams used primarily by hls.js [2]. Apple’s HLS examples page describes developer example streams and marks the Apple TV Trailer Basic example for testing only [3]. These are optional public-demo fixtures, not IPTV provider acceptance sources.

Result: **PASS for local/synthetic M3U harness behavior; real authorized M3U provider acceptance remains AUTHORIZED DATA BLOCKED.**

## 5. Xtream Validation

The local mock Xtream endpoint supports deterministic `player_api.php` responses for authentication-shaped metadata, live categories, live streams, VOD categories, Series categories, and short EPG shapes. Harness tests passed these local boundaries.

The previously supplied authorized Xtream control request returned HTTP 403 HTML before a JSON catalogue or media URL could be obtained. Phase 26 does not retry or bypass that restriction. Real Xtream authentication, catalogue retrieval, VOD, Series, EPG, and playback remain **AUTHORIZED DATA BLOCKED**.

## 6. MAG Validation

The local mock MAG/Stalker endpoint provides deterministic handshake, profile, channels, and create-link response shapes on loopback. This proves that the harness can be pointed at a local protocol fixture without inventing a production endpoint.

No authorized MAG/Stalker portal, MAC/session fixture, or stream resource was available. Real MAG discovery, handshake, profile, catalogue, stream resolution, and playback are **AUTHORIZED DATA BLOCKED**. No undocumented watchdog endpoint or Enigma2 mapping was added.

## 7. LIVE Playback

Synthetic LIVE mode produces repeated forward media-time samples from a deterministic clock and marks the GUI as responsive. The harness accepts a real LIVE stream only through explicit authorized environment configuration and passes the resolved resource to the existing `VlcPlayerAdapter`.

No authorized LIVE stream was available. Therefore real LIVE media-time progression is **NOT TESTED** and no provider compatibility claim is made.

## 8. VOD Playback

Synthetic and public-demo VOD inputs are supported by the harness configuration. VOD acceptance requires repeated forward `get_position_ms()`/duration samples from the existing player boundary; a successful `play()` call or a `Playing` state alone is insufficient.

The selected public Mux Big Buck Bunny playlist was reachable over credential-free HTTPS and returned ordinary M3U8 content. The real libVLC smoke attempt in the Linux sandbox was classified as an **ENVIRONMENTAL BLOCKER** because native `libvlc_new` was unavailable. No real VOD media-time evidence was captured.

## 9. Series Playback

The local mock Xtream boundary includes Series category response shapes, and the harness schema supports `EPISODE` content classification. Real Series → Season → Episode playback, completion, adjacent episode behavior, and media-time progression require an authorized Xtream or other provider catalogue and media URL.

No such data was available. Result: **NOT TESTED / AUTHORIZED DATA BLOCKED.**

## 10. Media-Time Evidence

Each sample record contains the required sanitized fields: timestamp, provider type, content type, stream identifier hash, VLC state, media time, position, duration, buffering state, recovery state, and GUI responsiveness.

The synthetic evidence ledger is `build/PHASE26_REAL_MEDIA_TIME_EVIDENCE.json`. Synthetic progress, stall, interruption, and switching scenarios all passed. The public-demo real-mode attempt produced an environmental blocker rather than a fabricated media-time PASS.

| Evidence class | Result |
|---|---|
| Synthetic media-time progression | **PASS** |
| Synthetic stall/recovery markers | **PASS** |
| Public-demo playlist availability | **PASS — availability only** |
| Public-demo libVLC media-time progression in Linux sandbox | **ENVIRONMENTAL BLOCKER** |
| Authorized provider media-time progression | **NOT TESTED — AUTHORIZED DATA BLOCKED** |

## 11. Channel Switching

The mock switching scenario exercises deterministic current-stream ownership and GUI responsiveness markers. The production stale-generation and current-playback protections remain unchanged and are covered by existing tests.

A real A → B → C → A sequence was not run because no authorized catalogue or stream set was available. Real current-stream-only rendering, stale suppression under network conditions, orphan detection, and Windows GUI responsiveness are **NOT TESTED**.

## 12. Stall Detection

The synthetic stall scenario holds media time constant at a controlled sample, records a `stalled` marker, records one bounded recovery attempt, and then records resumed forward progress. This validates the harness evidence shape and the existing production liveness decision contract without modifying production code.

A real IPTV silent stall was not reproduced. Real stall acceptance remains **NOT TESTED — AUTHORIZED MEDIA REQUIRED**.

## 13. Recovery

The harness records `recovery_state` and `recovery_attempts` while leaving recovery ownership in the existing `VlcPlayerAdapter`. Synthetic interruption/recovery passed. The real mode does not introduce an alternate recovery loop; it observes the application’s existing state and position APIs.

Controlled real interruption was not performed because no authorized stream was available. Result: **NOT TESTED — CONTROLLED INTERRUPTION UNAVAILABLE**.

## 14. Resource Monitoring

The Phase 26 harness provides sanitized evidence records but does not claim process, RAM, thread, handle, CPU, or VLC object trend measurements from a real A → B → C → A sequence. Those measurements require the exact published Windows executable, a configured authorized catalogue, and a Windows-capable resource sampler.

Result: **NOT TESTED.** Normal synthetic test execution is not classified as a memory-leak result.

## 15. GUI Responsiveness

Synthetic scenarios mark GUI responsiveness true because they run without blocking the local harness loop. The real mode calls `QApplication.processEvents()` between samples and records whether the sampling iteration remains below the configured responsiveness threshold.

The public-demo real attempt could not instantiate native libVLC in the Linux sandbox, so no real GUI/video-surface responsiveness result exists. Windows GUI responsiveness remains **NOT TESTED** for authorized IPTV playback.

## 16. Windows Validation

Phase 26 preserves the rule that Linux is not equivalent to Windows real-playback acceptance. The existing hosted Windows Portable EXE workflow previously passed packaging, native VLC, application, path, and smoke gates for the unchanged application state. Those gates do not provide provider media-time evidence.

The new real-mode harness is Windows-ready in design because it uses the existing Qt/native surface and `VlcPlayerAdapter`, but no authorized stream configuration was available on a Windows runner. Result: **NOT TESTED — WINDOWS AUTHORIZED MEDIA REQUIRED**.

## 17. Regression Gates

| Gate | Result |
|---|---|
| Focused harness/provider/VLC selection | **PASS — 87 collected and executed** |
| Official non-presentation corpus | **PASS — 890 collected and executed** |
| Ruff | **PASS** |
| Black | **PASS — 374 files unchanged** |
| MyPy source | **PASS — 221 source files** |
| MyPy harness | **PASS — 2 files** |
| Bandit | **PASS** with existing informational warnings only |
| Security regression selection | **PASS — 16 tests** |
| Secret scan | **PASS** |
| Prohibited Enigma2 scan | **PASS** |
| `git diff --check` | **PASS** |

The official non-presentation corpus excludes the known presentation-only collection surface according to repository convention. No production test was weakened or skipped because of Phase 26.

## 18. Defects

No reproducible production defect was established. The first public-demo real-mode attempt exposed a harness error path: missing native `libVLC` caused an uncaught initialization exception. The harness was corrected to classify that condition as **ENVIRONMENTAL BLOCKER** and the public-demo smoke was rerun successfully to the classified result. This was a harness-only fix, not a production playback change.

The synthetic harness tests and all final quality gates passed after the correction.

## 19. Blockers

The exact blockers are: no authorized populated M3U/M3U8 provider source, no authorized MAG/Stalker portal/session fixture, prior authorized Xtream HTTP 403 HTML before catalogue retrieval, no authorized real media URL, native libVLC unavailable in the Linux sandbox for public-demo playback, and no Windows runner configured with authorized media for real acceptance.

These blockers prevent real LIVE/VOD/EPISODE media-time acceptance, real interruption/recovery, real channel switching, EPG acceptance, and resource trend measurement. They are not converted into PASS.

## 20. Final Classification

# C — PROVIDER VALIDATION BLOCKED

The harness itself is ready for repeatable local and authorized execution. Real provider acceptance is not A because no authorized media-time evidence exists. It is not B because no provider/content type has produced real media-time PASS evidence. It is not D because no real stream reached the media layer with a reproducible production defect.

The precise statement is: **the Phase 26 acceptance harness is implemented and locally verified; real authorized provider playback remains blocked and commercial IPTV compatibility is not certified.**

## 21. Release Recommendation

**DO NOT CREATE A RELEASE.** Do not increment version, create a tag, modify `v0.1.5`, replace assets, modify CI gates, or change README badges. Phase 26 is validation infrastructure and evidence collection only.

The next required action is to run the harness on Windows with an authorized M3U/M3U8, Xtream, or MAG/Stalker configuration. The result can be upgraded only when repeated real media-time samples prove progression for the tested content type and the full acceptance matrix is executed.

## References

[1]: https://github.com/video-commander/public-test-streams "video-commander/public-test-streams — Public video streams for testing"
[2]: https://test-streams.mux.dev/ "Mux Test HLS Streams"
[3]: https://developer.apple.com/streaming/examples/ "Apple HTTP Live Streaming Examples"
