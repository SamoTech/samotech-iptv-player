# PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT

## 1. Executive Summary

Phase 25 validated whether the existing libVLC-based SamoTech IPTV Player can be accepted against authorized populated IPTV sources. The locked architecture was inspected and preserved: libVLC through `python-vlc` remains the only media backend, the existing `VlcVideoSurface` remains the sole native surface, `PlaybackResource`/`ResolvedPlayback` contracts remain intact, and the existing typed liveness/recovery controller remains the only recovery architecture.

Real-provider acceptance could not be completed. No authorized populated M3U/M3U8 source or MAG/Stalker portal fixture was available. The authorized Xtream control-plane probe, using user-supplied credentials only in process memory, returned HTTP 403 HTML for both control and server-info requests before a JSON catalogue or media URL could be obtained. Therefore no real provider media-time samples, real buffering observations, real interruption recovery, or commercial compatibility claim is valid.

Provider-neutral and synthetic boundaries passed, including 27 M3U tests, 55 Xtream tests, 27 MAG tests, 72 deterministic VLC/orchestration tests, focused presentation/stale-switching tests, the official 885-test non-presentation corpus, and the existing quality/security gates. These results do not substitute for real provider playback evidence.

## 2. Repository State

The repository was inspected at the synchronized Phase 24 state. `HEAD` and `origin/main` were equal at the beginning and remained equal after validation. The worktree is clean apart from ignored build evidence. Application version `0.1.5`, annotated tags `v0.1.4` and `v0.1.5`, existing release assets, CI workflows, and README badges were preserved.

The prior Phase 24 classification remains **UI AUDIT PASS WITH MINOR FINDINGS**. Phase 25 found no interface regression requiring reopening that work. The Phase 23 release audit remains preserved; no new version, tag, release, or asset was created.

## 3. Architecture Verification

The verified dependency map is:

```text
Provider input
  → M3U / Xtream / MAG provider adapter
  → PlaybackTarget and PlayPlaybackTarget
  → ResolvedPlayback + PlaybackResource + TransportMetadata
  → VlcPlayerAdapter
  → libVLC media/player
  → VlcVideoSurface native window handle
  → PlayerShell typed UI state and controls
  → generation/session-scoped buffering, liveness, and recovery
```

The player adapter owns the existing media generation, session token, native event subscriptions, buffering watchdog, liveness heartbeat, bounded retry/window/backoff policy, and safe diagnostics. The PlayerShell renders typed state and does not expose resolved URLs, credentials, cookies, or raw backend exceptions.

No mpv, FFmpeg playback backend, browser playback, QtMultimedia playback, second player instance, second recovery controller, provider architecture rewrite, Enigma2 service mapping, or speculative media-plane header behavior was introduced.

## 4. Test Authorization Boundary

Real provider testing was restricted to authorized data. The user-supplied Xtream authorization was used only for a redacted control-plane probe, with credentials held in process environment and never written to repository files or output. The probe reported only the sanitized endpoint scheme/host, HTTP status, content type, byte count, and a short redacted response prefix.

No authorized populated M3U/M3U8 file or URL was available in the workspace. No authorized MAG/Stalker portal, MAC address, session fixture, or stream resource was available. Public credential discovery, scraping, authentication bypass, brute force, arbitrary commercial probing, and leaked credentials were not used.

## 5. M3U Results

| M3U feature | Result | Evidence |
|---|---|---|
| Authorized populated import | **BLOCKED — AUTHORIZED TEST DATA REQUIRED** | No authorized populated M3U/M3U8 source in workspace |
| Detection, parser, malformed-entry and registration boundaries | **PASS — 27 synthetic tests** | `build/PHASE25_M3U_VALIDATION.txt` |
| Name/group/logo/tvg/User-Agent/Referer mapping | **PASS — synthetic only** | Existing parser and adapter tests |
| Real catalogue/categories/search/favorites | **BLOCKED** | No populated source |
| Real multiple-stream VLC playback | **BLOCKED** | No authorized stream resource |
| Sustained real stability and stall recovery | **NOT TESTED** | Requires authorized stream and Windows runtime |

The synthetic M3U tests prove the provider-neutral parser and handoff boundaries only. They do not prove a real playlist’s metadata quality or real media continuity.

## 6. Xtream Results

The authorized control-plane probe made two requests using in-memory user-supplied credentials. Both returned HTTP `403`, `text/html`, approximately 4.4 KB, with an access-denied HTML prefix rather than JSON. No catalogue request could proceed to live, VOD, Series, or EPG validation, and no media URL was obtained.

| Xtream feature | Result | Evidence |
|---|---|---|
| Authorized authentication/control response | **BLOCKED — HTTP 403 HTML** | `build/PHASE25_XTREAM_CONTROL_PROBE.txt` |
| Synthetic URL/resource and provider boundary | **PASS — synthetic only** | Existing adapter/request-builder tests |
| Synthetic catalogue translation and realistic variations | **PASS — 55 tests** | `build/PHASE25_XTREAM_SYNTHETIC_VALIDATION.txt` |
| Live categories/streams/metadata/logos/playback | **BLOCKED** | Control plane rejected before catalogue retrieval |
| Movies/VOD/playback/seek/pause/resume/restart | **BLOCKED** | No catalogue or media URL |
| Series/seasons/episodes/playback/completion | **BLOCKED** | No catalogue or media URL |
| EPG/current/next/channel association | **BLOCKED / NOT TESTED** | No usable EPG payload |

The 403 is classified as an external provider-access blocker, not as an application playback defect. Xtream URL expiry/refresh behavior and provider-specific media headers remain unproven.

## 7. MAG/Stalker Results

No authorized MAG/Stalker portal or device/session data was available. Accordingly, portal configuration, handshake, authentication, profile/device behavior, catalogue retrieval, stream resolution, VLC playback, session expiry, and provider-specific recovery were not run against a real source.

The existing implementation was inspected. Its supported boundary remains profile-driven handshake/session handling, selected control-plane requests, catalogue translation, `create_link` stream resolution, and validation of returned HTTP(S)/RTSP/RTMP URLs. Synthetic MAG coverage passed 27 tests across the adapter, domain translator, and provider integration suites.

No undocumented watchdog endpoint, alternate protocol, Enigma2 selector, or provider-specific workaround was invented. Any requirement beyond the implemented profile/session/create-link path remains **REQUIRES AUTHORIZED PROVIDER VALIDATION** and must be classified as `UNIMPLEMENTED`, `DEFECT`, or `PROVIDER-SPECIFIC REQUIREMENT` only after authorized evidence exists.

## 8. VLC Playback Evidence

The deterministic VLC/orchestration selection passed 72 tests, including 48 VLC adapter tests, playback controls, playback-target orchestration, and registered-playback coverage. The focused presentation/stale-switching selection passed two tests. The Linux native VLC lifecycle probe correctly reported `SKIP reason=windows_required` because it is a Windows-native probe.

The previous hosted Windows Portable EXE workflow for the unchanged Phase 24 implementation passed the bundled VLC runtime, native VLC lifecycle, packaged EXE smoke, Qt/application smoke, path/CWD, artifact, and SHA256 gates. Those gates prove packaged runtime and deterministic native lifecycle behavior; they did not open an authorized IPTV URL.

No real authorized LIVE, MOVIE, or EPISODE stream was resolved during Phase 25. Therefore no real provider VLC acceptance is reported as PASS.

## 9. Media-Time Progress Evidence

No real provider media-time samples were captured. The evidence set contains no authorized stream URL, no repeated `get_time()` observations from a real IPTV source, no real `get_position()` series for VOD/episode playback, and no real duration observation.

The synthetic VLC adapter tests prove the intended decision behavior: forward `get_time()` progress resets the stall deadline, unchanged media time can route through `STALLED`, and liveness tasks are cancelled on stop, channel switch, recovery, and shutdown. This is provider-neutral behavioral evidence, not real media continuity.

| Required real evidence | Result |
|---|---|
| LIVE media time advances over repeated samples | **BLOCKED — AUTHORIZED MEDIA REQUIRED** |
| MOVIE/EPISODE media time and position advance consistently | **BLOCKED — AUTHORIZED MEDIA REQUIRED** |
| Real buffering/reconnecting samples | **NOT TESTED** |
| Real final state after sustained playback | **NOT TESTED** |

## 10. Stall Detection

Synthetic stall detection is covered by the existing heartbeat tests. The adapter uses libVLC `get_time()` rather than process liveness or `is_playing()` as the media-health signal. A forward position update resets the deadline, while unchanged valid media time beyond the configured threshold routes through the existing bounded recovery controller with reason `STALLED`.

A real IPTV silent-stall reproduction was not possible because the authorized provider sources were unavailable or rejected at control-plane access. Therefore **real stall detection: NOT TESTED**. No real stream was declared stalled or healthy without samples.

## 11. Recovery Evidence

Synthetic recovery evidence passed for bounded `STALLED`, `ENCOUNTERED_ERROR`, LIVE EOF, buffering timeout, stale generation, intentional stop, retry budget, recovery window, backoff, and typed non-live completion/error behavior. Recovery remains generation/session scoped and uses the current playback metadata through the existing single recovery architecture.

Real interruption recovery was not tested. The specification’s controlled interruption sequence could not safely be performed because no authorized stream was available. The exact classification is **NOT TESTED — CONTROLLED INTERRUPTION NOT AVAILABLE**, not PASS and not a fabricated failure.

## 12. Channel Switching

Synthetic channel/provider switching tests passed stale identity invalidation, current-generation protection, stale result suppression, and singular native surface ownership. The PlayerShell and application tests prove that stale async results cannot replace current selection in the deterministic test harness.

A real A → B → C → A → B → C playback sequence was not run because no authorized catalogue or stream resource was available. Real duplicate-media-instance, current-stream-only, and multi-channel media-time behavior are **NOT TESTED**.

## 13. VOD Playback

Synthetic Xtream VOD DTO translation and URL/resource boundary tests passed, and the typed VOD completion semantics are covered by the VLC adapter tests. The PlayerShell exposes VOD seek, pause, resume, stop, restart, position, and duration through the existing player port when a real VOD item is present.

No authorized VOD catalogue, artwork payload, media URL, or real movie stream was obtained. Movie playback, seek, pause, resume, stop, restart, and real position/duration progression are therefore **BLOCKED / NOT TESTED**.

## 14. Series/Episode Playback

Synthetic Series metadata variations, seasons, episodes, episode identity, adjacent episode behavior, and typed episode completion are covered by existing tests. The Phase 24 native PlayerShell probe also passed Series → Season → Episode navigation using deterministic fixtures.

No authorized Series catalogue or episode media URL was obtained. Real episode playback, previous/next episode behavior against a provider, and real episode completion are **BLOCKED / NOT TESTED**.

## 15. EPG

The application exposes provider EPG and XMLTV paths, and synthetic provider/application tests cover DTO and boundary behavior. No authorized Xtream JSON catalogue or EPG response was available because the control-plane requests returned HTTP 403 HTML. No authorized M3U or MAG EPG source was available.

EPG retrieval, current programme, next programme, and channel association are therefore **BLOCKED / NOT TESTED**. No EPG PASS is claimed.

## 16. Error Handling

The deterministic error matrix passed safe error-boundary, invalid credential, malformed response, unsupported playback, provider authentication failure, and bounded VLC error tests. The UI and diagnostics do not expose passwords, tokens, cookies, authorization headers, credential-bearing URLs, or raw stack traces.

| Failure condition | Classification in this phase |
|---|---|
| Authorized Xtream HTTP 403 HTML | **EXPECTED EXTERNAL BLOCKER / PROVIDER VALIDATION BLOCKED** |
| Missing authorized M3U source | **BLOCKED** |
| Missing authorized MAG portal | **BLOCKED** |
| Malformed provider payloads in synthetic fixtures | **EXPECTED HANDLED** |
| Invalid credentials in synthetic/provider-boundary tests | **EXPECTED HANDLED** |
| Invalid media resource in synthetic VLC tests | **EXPECTED HANDLED / UNSUPPORTED as typed** |
| Real stream stall | **NOT TESTED** |
| Real session expiry | **NOT TESTED** |
| Real provider API timeout/unreachable server | **NOT TESTED against authorized source** |

## 17. Security

The authorized Xtream credentials were passed through process environment to a temporary probe and were not stored in the repository. The probe output contains no username, password, credential-bearing URL, response body, token, cookie, MAC, or authorization header.

The Phase 25 secret scan found no authorized credentials in tracked source/test/report files. The prohibited Enigma2-value scan found no `4097`, `5001`, `5002`, `8193`, `eServiceReference`, or `playService` values in source/tests. Existing safe diagnostics and error-boundary tests passed.

## 18. Resource/Memory Observations

No real repeated provider playback sequence was available, so process count, memory, handles, threads, VLC media object lifetime, orphaned timers, and orphaned recovery task trends were not measured in Phase 25. A memory leak is not inferred from the absence of this measurement.

The static architecture still shows one `VlcVideoSurface` owner and one injected player boundary. Synthetic stale-generation and lifecycle tests pass, but they are not substitutes for a Windows multi-minute A → B → C resource trend.

## 19. Regression Results

| Gate | Result |
|---|---|
| M3U synthetic boundary tests | **PASS — 27** |
| Xtream synthetic boundary/catalogue tests | **PASS — 55** |
| MAG synthetic boundary/integration tests | **PASS — 27** |
| Deterministic VLC/orchestration tests | **PASS — 72** |
| Focused presentation/stale-switching tests | **PASS — 2** in the Phase 25 selection |
| Official non-presentation corpus | **PASS — 885** |
| Ruff | **PASS** |
| Black | **PASS — 372 files unchanged** |
| MyPy | **PASS — 221 source files** |
| Bandit | **PASS** with existing informational warnings only |
| Security regression | **PASS — 14** |
| Secret scan | **PASS** |
| Prohibited Enigma2 scan | **PASS** |
| `git diff --check` | **PASS** |
| Hosted CI | **PASS** — `32177305266` for the unchanged implementation state |
| Hosted CodeQL | **PASS** — `32177305185` for the unchanged implementation state |
| Windows Portable EXE | **PASS** — `32177305081` for the unchanged implementation state |

No implementation change was made in Phase 25, so no new CI, CodeQL, or Windows run was required by the specification’s “after any implementation change” rule. The cited hosted runs validate the exact current implementation state before this report-only validation work.

## 20. Code Changes

**NO IMPLEMENTATION CHANGE REQUIRED.** No reproducible application defect was found because no real provider playback path reached the media layer. No source, provider, playback, recovery, UI, release, CI, packaging, or security code was changed.

Phase 25 added only sanitized validation evidence and documentation artifacts: `build/PHASE25_REPOSITORY_FORENSIC_REVIEW.md`, `build/PHASE25_FORENSIC_BASELINE.txt`, `build/PHASE25_DEPENDENCY_MAP.txt`, `build/PHASE25_AUTHORIZED_SOURCE_INVENTORY.txt`, `build/PHASE25_XTREAM_CONTROL_PROBE.txt`, provider validation logs, `build/PHASE25_PROVIDER_PLAYBACK_MATRIX.md`, `build/PHASE25_PROVIDER_PLAYBACK_EVIDENCE.json`, and this report. These are validation artifacts, not playback implementation changes.

## 21. Remaining Blockers

The complete acceptance blockers are the absence of an authorized populated M3U source, absence of an authorized MAG/Stalker portal/session fixture, the authorized Xtream HTTP 403 HTML response before catalogue retrieval, and the absence of a real authorized media URL. These blockers prevent real media-time progression, real buffering, real stall/recovery, real channel switching, real VOD/Series playback, EPG validation, controlled interruption, and memory/resource trending.

The Linux environment also cannot execute the native Windows VLC lifecycle probe. The existing hosted Windows package/runtime gates passed, but they do not provide authorized IPTV media continuity.

## 22. Final Classification

# C — PROVIDER VALIDATION BLOCKED

This classification is exact. It is not **A — REAL PROVIDER PLAYBACK ACCEPTED** because no real authorized stream produced media-time evidence. It is not **B — PARTIAL PROVIDER ACCEPTANCE** under this Phase 25 matrix because the only authorized provider reached returned HTTP 403 before catalogue/media validation, while M3U and MAG authorized data were unavailable. It is not **D — PLAYBACK DEFECT FOUND** because no real stream reached the media layer and no reproducible defect was established.

The correct technical statement is: **provider-neutral playback reliability remediation remains covered by deterministic tests and hosted packaging/runtime evidence, but real authorized IPTV provider acceptance is blocked and commercial compatibility is not certified.**

## 23. Release Recommendation

**DO NOT RELEASE FROM PHASE 25.** Preserve `v0.1.5`, its assets, tags, CI gates, and README badges exactly as they are. Do not create a new tag or GitHub Release from this validation phase.

The next phase should supply authorized populated M3U and/or MAG data, or restore an authorized Xtream endpoint that returns the expected JSON control response. It should then run the exact published Windows EXE against authorized live and VOD/Series media, capture repeated media-time samples, verify GUI responsiveness, perform safe channel switching, exercise bounded recovery and controlled interruption where possible, and measure resource trends before any real-provider acceptance or release recommendation is upgraded.

## Evidence References

1. `build/PHASE25_REPOSITORY_FORENSIC_REVIEW.md` — repository and architecture review.
2. `build/PHASE25_DEPENDENCY_MAP.txt` — provider-to-player symbol map.
3. `build/PHASE25_AUTHORIZED_SOURCE_INVENTORY.txt` — authorized source inventory.
4. `build/PHASE25_XTREAM_CONTROL_PROBE.txt` — redacted authorized Xtream HTTP 403 evidence.
5. `build/PHASE25_M3U_VALIDATION.txt` — M3U blocker and synthetic validation.
6. `build/PHASE25_XTREAM_SYNTHETIC_VALIDATION.txt` — Xtream synthetic validation.
7. `build/PHASE25_MAG_VALIDATION.txt` — MAG blocker and synthetic validation.
8. `build/PHASE25_VLC_PLAYBACK_EVIDENCE.txt` — real-media blocker, deterministic VLC tests, and Linux native-probe skip.
9. `build/PHASE25_ERROR_MATRIX_TESTS.txt` — deterministic error matrix tests.
10. `build/PHASE25_REGRESSION_GATES.txt` — local regression and quality/security gates.
11. `build/PHASE25_PROVIDER_PLAYBACK_MATRIX.md` — required provider/playback matrix.
12. `build/PHASE25_PROVIDER_PLAYBACK_EVIDENCE.json` — sanitized machine-readable evidence.
13. `VLC_IPTV_PLAYBACK_REMEDIATION_AUDIT.md` — prior remediation and release classifications.
14. `PHASE24_UI_UX_AUDIT.md` — preserved prior interface classification.
15. Hosted CI run `32177305266` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305266
16. Hosted CodeQL run `32177305185` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305185
17. Hosted Windows Portable EXE run `32177305081` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305081
