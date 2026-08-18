# IPTVnator-Informed Playback Reliability Implementation Audit

**Repository:** [SamoTech/samotech-iptv-player][1]
**Reference implementation:** [4gray/iptvnator][2]
**Audit scope:** Phase 3 IPTVnator-informed protocol and playback reliability engineering
**Implementation commits:** `91d817b` and `7498349`
**Audit date:** 2026-08-18
**Author:** **Manus AI**

> **Final status:** **IMPLEMENTED at the tested provider-neutral boundary; PARTIAL for provider-specific media behavior; REQUIRES AUTHORIZED PROVIDER VALIDATION for populated Xtream/MAG media contracts and watchdog behavior; NOT TESTED on a real consumer Windows 10/11 client.**

## 1. Executive summary

This audit used IPTVnator as an external engineering reference, not as a source to copy. The applicable ideas were explicit separation of source context, playback payload, media engine, evidence, and recovery; stable logical identity independent of temporary stream URLs; stale-generation protection; bounded recovery; and diagnostics that explain media failure without exposing credentials.[2] [3] [4]

SamoTech remains a **Windows + PySide6 + libVLC** application with provider-neutral Python ports. No Angular, TypeScript, Electron, browser playback engine, MPV integration, or IPTVnator code was introduced. The implementation work was limited to preserving validated `PlaybackResource` context through `ResolvedPlayback`, adding safe transport-type and error-classification fields to VLC telemetry, and strengthening deterministic regression coverage.

The earlier Phase 2 work remains in force: supported M3U User-Agent and Referer attributes are mapped into ephemeral `TransportMetadata`; Xtream and MAG media-plane metadata remain URL-only until provider evidence proves that additional headers or cookies are required; and bounded `EncounteredError` recovery is part of the existing live recovery policy. Live/VOD cache defaults were not changed because no evidence demonstrated that a larger or separate cache is the correct remedy.

The final hosted Windows validation run **32156943241** passed all blocking gates for commit `749834995020e77a24ab876e917dcd041f8271e0`. Its generated artifact was named `SamoTech-IPTV-Player-Windows-x64-build-7498349.exe` and the workflow recorded SHA256 `463d11096a3c36e59e1c0ac330a2d8cc315c317f7b9e77e1cc240372008f2033`.[5] This proves packaged startup, bundled VLC lifecycle, Qt/application smoke, diagnostics, sanitized-PATH execution, artifact auditing, and checksum generation on the hosted Windows runner. It does **not** prove universal provider compatibility or long-lived playback against a populated commercial account.

## 2. IPTVnator files studied

The reference repository was cloned and inspected directly. The audit reviewed the playback recovery session, pure recovery policy, recovery controller, player service, typed playback state, embedded-inline playback architecture, scoped stream-header service, Xtream URL service, playlist utilities, playback interfaces, and parsed-playlist interfaces. The principal reference files were:

| Area | IPTVnator source or document | Finding used in this audit |
|---|---|---|
| Recovery ownership | `libs/ui/playback/src/lib/web-player-view/playback-recovery-session.ts` | Recovery state belongs to a playback session, not to persistent player settings. |
| Recovery policy | `libs/ui/playback/src/lib/web-player-view/web-player-recovery-policy.ts` | Recovery is a pure decision over evidence, session identity, generation, and attempt state. |
| Recovery orchestration | `libs/ui/playback/src/lib/web-player-view/web-player-recovery-controller.ts` | Stale completions and session changes are explicitly guarded. |
| Player abstraction | `apps/web/src/app/services/player.service.ts` | Engine-specific behavior is behind a player service boundary. |
| Typed playback state | `libs/ui/playback/src/lib/web-player-view/web-player-playback-state.ts` | Playback context contains URL-independent identity, media hints, and diagnostic state. |
| Architecture contract | `docs/architecture/embedded-inline-playback.md` | Stable identity, safe evidence, recovery privacy, and scoped transport ownership are documented as separate concerns. |
| Scoped headers | `libs/ui/playback/src/lib/web-player-view/electron-stream-headers.service.ts` | Request-header ownership is scoped to playback transport rather than globally applied. |
| Xtream URL behavior | `libs/portal/xtream/data-access/src/lib/services/xtream-url.service.ts` | API/control-plane URL construction is distinct from playback state and media-engine behavior. |
| M3U parsing | `libs/shared/m3u-utils/src/lib/playlist.utils.ts` | Playlist metadata and media URL handling are separate from the player engine. |
| Typed payloads | `libs/shared/interfaces/src/lib/portal-playback.interface.ts` and `parsed-playlist.interface.ts` | Parsed content, media metadata, and source identity are represented as typed payloads. |

The reference findings were recorded in [`build/PHASE3_IPTVNATOR_EXTERNAL_FINDINGS.md`](build/PHASE3_IPTVNATOR_EXTERNAL_FINDINGS.md) and compared with the SamoTech inspection ledger in [`build/PHASE2_INSPECTION_FINDINGS.md`](build/PHASE2_INSPECTION_FINDINGS.md).

## 3. IPTVnator architecture findings

IPTVnator’s useful architecture can be summarized as:

```text
SOURCE
  → typed playback context
  → stable playback session identity
  → engine capability and media payload
  → structured evidence
  → ranked, bounded recovery
  → diagnostics that exclude secrets
```

The most important observation is that a healthy application process and a healthy media session are different facts. A GUI can remain responsive while the media engine is buffering, stopped, or emitting an error. Recovery therefore needs evidence tied to a logical playback session and media generation instead of a blind global restart.

The reference also treats temporary stream URLs as transport material rather than durable identity. A refresh or URL change must not create a new logical content item, and an old asynchronous completion must not recover or overwrite a newer playback session. These principles align with SamoTech’s existing provider-scoped `PlaybackResource` identities and public player generation/session guards.[2] [3]

## 4. Useful concepts adopted

| Concept | SamoTech implementation | Classification |
|---|---|---|
| Stable logical identity | `PlaybackResource` is carried through optional `ResolvedPlayback.resource`; provider ID, media type, canonical content ID, and opaque resource ID remain separate from the temporary URL. | **IMPLEMENTED** |
| Typed playback payload | `ResolvedPlayback` carries URL, ephemeral `TransportMetadata`, and optional resource context while retaining URL-only compatibility. | **IMPLEMENTED** |
| Scoped transport ownership | M3U metadata is mapped only when the parser recognizes supported aliases; Xtream/MAG control-plane headers are not automatically forwarded to libVLC. | **IMPLEMENTED / PARTIAL** |
| Structured media evidence | VLC telemetry includes media generation, state/reason, elapsed media timing, event sequence, provider/content labels, transport type, error classification, and recovery attempt/delay fields. | **IMPLEMENTED** |
| Stale completion protection | Existing media-generation and session-token checks remain the gate for recovery and native event effects. | **PROVEN** |
| Recovery attempt ownership | Recovery counters and time windows remain per live playback lifecycle, separate from persistent player settings. | **PROVEN** |
| Finite policy | Buffering watchdog, EOF, unexpected STOPPED, and EncounteredError recovery are bounded by attempt count, time window, delay, and current generation/session. | **IMPLEMENTED / PROVEN BY TESTS** |
| Safe diagnostics | Provider/content labels pass through bounded safe-label handling; URLs, credentials, cookies, MAC, tokens, and Authorization values are not logged. | **IMPLEMENTED / PROVEN BY TESTS** |

## 5. Concepts explicitly not adopted

SamoTech did **not** copy IPTVnator code or port its Angular/TypeScript architecture. Browser playback engines such as HTML5, Video.js, ArtPlayer, hls.js, Shaka, mpegts.js, and browser/VHS pipelines were not introduced. Electron, MPV, external VLC processes, and a multi-engine capability selector were not introduced. SamoTech continues to use one provider-neutral `PlayerPort` backed by one shared libVLC adapter.

KiddaC’s Enigma2 service types `1`, `4097`, `5001`, `5002`, and `8193` were also not adopted. Those values select Enigma2 service/player backends; they are not VLC protocols or media options. KiddaC’s EStalker/XStreamity request sequencing and Stalker/Xtream behavior remain protocol references only.[6] [7]

No blind URL-format copying, generic portal-header forwarding, automatic MAG watchdog endpoint, larger default cache, browser-only recovery technique, or persistent credential-bearing playback identity was added.

## 6. SamoTech baseline

Before the Phase 3 changes, the repository already had a provider-neutral `ResolvedPlayback`/`PlayerPort` boundary, typed playback state, live buffering watchdog, EOF and unexpected STOPPED recovery, one-shot software fallback for immediate start failure, M3U extended metadata parsing, Xtream live/VOD/series resolution, MAG/Stalker session/profile infrastructure, safe logging, and Windows packaged VLC validation.

The baseline focused test suite was recorded in [`build/PHASE2_BASELINE.md`](build/PHASE2_BASELINE.md). Phase 2 had already established that the transport metadata model could carry headers, User-Agent, Referer, protocol hint, and container hint, but provider-specific media metadata was not automatically populated. It also established that ordinary buffering must not immediately restart a healthy stream and that MAG watchdog behavior lacked authorized endpoint evidence.

The main Phase 3 information-loss point was the provider-to-player handoff: the unified playback use case knew the selected `PlaybackResource`, but the VLC adapter received only a URL-oriented resolved object. This weakened diagnostics because a media event could not identify the safe provider/content context that produced the temporary URL.

## 7. Code changes

The implementation changes are contained in two logical commits:

| Commit | Files | Change |
|---|---|---|
| `91d817b` | `playback.py`, `play_playback_target.py`, `vlc_player_adapter.py`, and related tests | Preserve optional credential-free `PlaybackResource` context across the provider-to-player handoff and assert it for live/movie/episode synthetic flows. |
| `7498349` | `vlc_player_adapter.py` and VLC regression tests | Add safe transport-type labels and explicit error classification to media, state, native-event, Playing, and bounded recovery telemetry; add regression assertions. |

`ResolvedPlayback.from_url()` remains backward-compatible by constructing empty transport metadata when no metadata is supplied and by accepting an optional resource. Legacy URL-only provider doubles and callers continue to work.

## 8. M3U changes

The M3U parser and adapter retain the Phase 2 implementation. Supported extended-M3U aliases are mapped as follows:

| Input attribute | Transport result | Classification |
|---|---|---|
| `http-user-agent` or `user-agent` | Ephemeral `TransportMetadata.user_agent` | **IMPLEMENTED** |
| `http-referrer` or `referrer` | Ephemeral `TransportMetadata.referrer` | **IMPLEMENTED** |
| `cookie` | Not propagated without repository/provider evidence | **REQUIRES AUTHORIZED PROVIDER VALIDATION** |
| Arbitrary attributes | Not inferred as media headers | **IMPLEMENTED SAFETY BOUNDARY** |

The M3U adapter still resolves only valid HTTP(S) playback URLs at the current application boundary. HLS/M3U8 demuxing is delegated to libVLC; no Python HLS engine was added. Parser tests cover supported metadata propagation, unsupported attribute exclusion, malformed/sensitive values, and adapter-level `ResolvedPlayback` propagation.

## 9. Xtream changes

The Xtream API and URL builders were audited against both SamoTech source and IPTVnator’s Xtream URL service. Current SamoTech URL semantics remain unchanged:

| Content | Current URL family | Status |
|---|---|---|
| Live | `/live/{username}/{password}/{id}.{ext}` | **IMPLEMENTED at repository URL-builder boundary** |
| Movie/VOD | `/movie/{username}/{password}/{id}.{ext}` | **IMPLEMENTED at repository URL-builder boundary** |
| Series episode | `/series/{username}/{password}/{id}.{ext}` | **IMPLEMENTED at repository URL-builder boundary** |

The implementation does not convert temporary Xtream URLs into persistent identity. The provider/resource identity remains separate from the credential-bearing URL, and diagnostics never log the URL. No provider-specific media cookies, User-Agent, Referer, or Authorization header was added because the repository does not contain evidence that the configured Xtream media server requires them. Populated VOD/Series and long-lived real-stream validation remain **REQUIRES AUTHORIZED PROVIDER VALIDATION**.

The deterministic synthetic suite covers player API-shaped catalogue data, live/VOD/series/episode translation, sparse and malformed records, URL extensions, concurrent refresh behavior, stale results, and current-context handoff. It does not substitute for a populated commercial account.

## 10. MAG/Stalker changes

The MAG/Stalker audit retained the existing profile-driven control plane: approved profile discovery, handshake, session/token lifecycle, cookies, MAC and Authorization handling inside infrastructure, catalogue/EPG, and `create_link` resolution. Control-plane headers are not automatically attached to media-plane `ResolvedPlayback` metadata.

The current application handoff remains HTTP(S)-only even though the legacy stream layer can validate additional returned schemes. MAG VOD, Series, and catch-up are not advertised by the application. No watchdog/event endpoint was invented. The watchdog status is **REQUIRES AUTHORIZED PROVIDER VALIDATION** because the repository does not have sufficient authorized evidence for the endpoint/profile contract and no live provider run was performed in Phase 3.

Synthetic MAG coverage remains focused on profile construction, handshake/session behavior, token expiry/refresh, `create_link`, stream normalization, control-plane headers, and redaction. It does not prove production portal compatibility.

## 11. VLC changes

The `VlcPlayerAdapter` remains the only media engine. It creates a new libVLC `Media` per playback generation and applies the existing supported options:

| Evidence or setting | libVLC behavior |
|---|---|
| Resolved URL | Passed to `media_new()`; never written to diagnostic logs. |
| Explicit HTTP headers | Added as `:http-header=name: value` only when present in typed transport metadata. |
| User-Agent | Added as `:http-user-agent=value`. |
| Referer | Added as `:http-referrer=value`. |
| Network caching | Existing configured default remains 1000 ms. |
| Hardware fallback | Existing automatic/software behavior remains; software fallback uses `:avcodec-hw=none`. |
| Qt output | Existing native Windows/Linux/macOS surface attachment remains unchanged. |

The Phase 3 change adds safe evidence labels. Transport type is taken from the typed protocol hint when present, otherwise from the URL scheme, without logging the URL itself. State records classify `ENCOUNTERED_ERROR`, `EOF`, `STOPPED`, and `BUFFERING_TIMEOUT` when those reasons drive a state decision. Native events include generation, event sequence, media delta, thread identity, provider/content labels, and transport type.[8]

## 12. Playback evidence model

The implementation now exposes a practical evidence stream through existing structured log records. The evidence is intentionally safe and bounded:

| Evidence | Current source | Classification |
|---|---|---|
| `RESOLVED` | Application/provider handoff | **PARTIAL**; resolution exists, but no new standalone log event was added. |
| `MEDIA_CREATED` | VLC media diagnostic record | **IMPLEMENTED** |
| `OPENING` | Native event diagnostic record | **IMPLEMENTED** when the binding exposes the event. |
| `BUFFERING` | Native event/state path and watchdog | **IMPLEMENTED** |
| `PLAYING` | Successful play/native state path | **IMPLEMENTED** |
| `BUFFERING_TIMEOUT` | Watchdog recovery reason | **IMPLEMENTED** |
| `ENCOUNTERED_ERROR` | Native event and state classification | **IMPLEMENTED** |
| `END_REACHED` | Native EndReached event and recovery path | **IMPLEMENTED** |
| `STOPPED` | Native Stopped event with intentional-action guard | **IMPLEMENTED** |
| `RECOVERING` | Bounded recovery state and recovery log | **IMPLEMENTED** |
| `RECOVERY_SUCCESS` | Recovery result/stability records | **IMPLEMENTED** |
| `RECOVERY_FAILED` | Recovery-abandoned or play-failure record | **IMPLEMENTED** |

Safe fields include provider ID, media type, canonical content ID, transport type, media generation, event sequence, elapsed media delta, state reason, error classification, retry count, recovery attempt, and recovery delay. Credential-bearing URLs, Xtream credentials, MAG MAC/token/cookie/Authorization data, and raw exception payloads are excluded.

The current logs provide time-to-media-create and time-to-event/Playing measurements through media-generation timestamps and elapsed fields. A separate durable `time_since_last_playing` metric is not persisted; this remains a recommended extension if field-level operational metrics are required.

## 13. Recovery policy

Recovery is evidence-driven and finite:

```text
native event or watchdog evidence
        ↓
classify current generation/session and intentional action
        ↓
recoverable live condition?
        ├─ no → preserve terminal/error state
        └─ yes → bounded delayed rebuild
                    ↓
              retry budget and recovery window
                    ↓
              current generation/session guard
                    ↓
              rebuild Media and retry
```

`BUFFERING` alone does not restart immediately. Prolonged buffering may trigger the existing watchdog. Unexpected `END_REACHED`, unexpected `STOPPED`, and `ENCOUNTERED_ERROR` may request a live recovery sequence when the current playback is live, the action was not intentional, no recovery task is already pending, the attempt budget is available, and the session/generation remains current. Delays are exponential and capped. The budget resets only after sustained Playing.

Intentional stop, application shutdown, channel switch invalidation, stale native callbacks, duplicate error callbacks, exhausted attempts, and expired recovery windows do not restart the newer or intentionally stopped playback. These cases are covered by deterministic tests.

## 14. Buffering strategy

The default network caching value remains **1000 ms** for both live and non-live media. No random increase was made. The current architecture can distinguish live versus VOD through `PlaybackResource.content_type`, but there is no controlled provider trace proving that a separate cache profile is the correct fix for the investigated symptom. Therefore the strategy is:

1. preserve the existing cache default;
2. observe buffering start, Playing, elapsed media delta, timeout, error, and recovery evidence;
3. classify provider/session expiry, missing media metadata, URL/container mismatch, network instability, and decode/output issues separately; and
4. add separate live/VOD settings only after controlled measurements demonstrate the need.

This is **IMPLEMENTED as a conservative policy** and **PARTIAL** as an operational diagnosis because libVLC state alone cannot identify the remote provider’s HTTP or session cause.

## 15. Tests

The required deterministic test matrix was executed without real credentials.

| Test scope | Result |
|---|---:|
| Focused final provider/player/VLC regression set | **109 passed** |
| VLC adapter regression suite after final telemetry | **40 passed** |
| Complete non-presentation corpus after final telemetry | **877 passed, 72 warnings** |
| Ruff | **PASS** |
| Black | **PASS** |
| MyPy source-only gate | **PASS — 221 source files** |
| Bandit | **PASS with existing nosec/comment warnings; no findings** |
| Secret/credential/scope audit | **PASS** |
| README badge block | **UNCHANGED** |
| Full broad Linux suite including presentation tests | **BLOCKED** — Qt/PySide6 collection segfault, exit 139 |
| pip-audit | **FAIL / PRE-EXISTING ENVIRONMENT BLOCKER** — pypdf 6.14.2, wheel 0.42.0, xhtml2pdf 0.2.14 findings |

The full-suite blocker is documented in [`build/PHASE2_FULL_TEST_BLOCKER.md`](build/PHASE2_FULL_TEST_BLOCKER.md). The crash occurs during collection of `tests/test_presentation_smart_import_dialog.py` while importing `PySide6.QtWidgets` in the available Linux sandbox. Presentation tests remain in the repository and were not deleted or weakened. The Windows workflow uses its established non-Qt corpus and passed it on the hosted Windows runner.

Additional regressions prove supported M3U metadata propagation, Xtream/MAG empty metadata boundaries, context preservation across live/movie/episode playback, stale-result protection, VLC header option construction, secret-safe diagnostics, transport-type telemetry, EncounteredError classification, duplicate-error suppression, retry budget, and intentional-stop behavior.

## 16. Windows validation

The final implementation commit `7498349` was validated by hosted Windows run [32156943241][5] on `windows-latest`.

| Hosted Windows gate | Result |
|---|---|
| Python/dependency installation | **PASS** |
| VLC 3.0.23 acquisition and SHA256 | **PASS** |
| `libvlc.dll`, `libvlccore.dll`, and 363 plugin DLLs | **PASS** |
| Ruff, Black, MyPy | **PASS** |
| Windows non-Qt corpus | **PASS** |
| Native VLC lifecycle | **PASS** |
| One-file PyInstaller build | **PASS** |
| Packaged-VLC EXE smoke | **PASS** |
| Qt/application EXE smoke | **PASS** |
| Startup diagnostics and `MAIN_WINDOW_SHOWN` | **PASS** |
| Sanitized PATH/outside-repository execution | **PASS** |
| Generated artifact audit | **PASS** |
| SHA256 and build metadata | **PASS** |
| Artifact upload | **PASS** |

The workflow recorded artifact `SamoTech-IPTV-Player-Windows-x64-build-7498349.exe` with SHA256 `463d11096a3c36e59e1c0ac330a2d8cc315c317f7b9e77e1cc240372008f2033`. A local transfer of the 135 MB hosted artifact exceeded the available terminal transfer bound, so this report treats the workflow-produced checksum as hosted-run evidence rather than claiming a second local byte-for-byte download verification.

This is **PROVEN/IMPLEMENTED** for the hosted Windows packaged lifecycle. It is **NOT TESTED** on the original real Windows 11 client, Windows 10, or a consumer endpoint with SmartScreen/antivirus behavior. The run’s smoke tests validate application and packaged-VLC readiness; they do not constitute long-lived commercial stream playback acceptance.

## 17. Real provider validation

No populated authorized Xtream or MAG acceptance was executed in Phase 3. The preserved sanitized Xtream probe record contains no usable populated result, and no provider credential names were present in the current environment. No live third-party account was used, no production payload was stored, and no real MAG watchdog trace was available.

| Provider/media area | Classification | Exact reason |
|---|---|---|
| M3U parser and supported metadata aliases | **IMPLEMENTED / PROVEN BY SYNTHETIC TESTS** | Deterministic parser and adapter fixtures cover supported aliases and safe exclusion. |
| Xtream API and URL builders | **IMPLEMENTED AT REPOSITORY BOUNDARY** | Synthetic catalogue and URL tests pass; populated commercial media behavior was not exercised. |
| Xtream media headers/cookies/session lifetime | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | No evidence proves the configured media server requires extra headers or cookies. |
| MAG handshake/profile/session/create_link | **PARTIAL / PROVEN BY SYNTHETIC TESTS** | Existing profile/session labs pass; no populated production portal acceptance. |
| MAG media-plane metadata | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Control-plane headers and tokens must not be forwarded automatically. |
| MAG watchdog/event keepalive | **REQUIRES AUTHORIZED PROVIDER VALIDATION** | Endpoint/profile contract is not established by repository evidence. |
| Commercial long-lived playback | **NOT TESTED** | No authorized populated provider run was performed. |

## 18. Security validation

The implementation preserves the repository’s credential boundaries. Xtream credentials and MAG MAC/token/cookies remain infrastructure-owned and are not included in `PlaybackResource` identity. Resolved URLs remain ephemeral and are not logged. VLC telemetry emits bounded safe labels only. The test suite includes sensitive-value canaries and nested-header redaction tests; the final secret scan found no authorized credentials in changed source, tests, documentation, or workflows.

Bandit completed without security findings, although it emitted existing warnings about `# nosec` markers and words in comments. Those warnings were not converted into suppressions or treated as new findings. `pip-audit` did not pass in the sandbox because the environment contains known vulnerable versions: `pypdf 6.14.2` with two 2026 advisories, `wheel 0.42.0` with CVE-2026-24049, and `xhtml2pdf 0.2.14` with a PYSEC advisory. No dependency version was changed because that would exceed the evidence-backed playback scope; this is an explicit remaining security blocker.

The README badge block was preserved byte-for-byte. Release tags and version metadata were not changed.

## 19. Remaining limitations and recommended next phase

The most important remaining work is authorized, sanitized, populated-provider validation on Windows. That work should capture redacted HTTP/media evidence for an Xtream account with live, VOD, and episode streams and for a compatible MAG/Stalker portal with a known profile and watchdog contract. It should determine whether the final media URL needs User-Agent, Referer, cookies, Authorization, a refreshed token, or a provider-specific keepalive. Any metadata should be added only to ephemeral transport context after the evidence is reproduced.

A future phase should also add a standalone `RESOLVED` evidence event and a durable, credential-free operational metric for `time_since_last_playing`, while preserving current generation/session guards. Separate live/VOD buffering profiles should be evaluated only through controlled traces. MAG VOD/Series/catch-up and provider-neutral timeshift should remain deferred until their control/media contracts are established.

The full Linux presentation collection segfault and pip-audit dependency findings should be resolved in their respective environments. Neither blocker was hidden, weakened, or misclassified as a playback success.

## 20. Final release decision

The implementation is **accepted for the current development/release boundary** represented by commits `91d817b` and `7498349`: provider context now survives the provider-to-player handoff, M3U supported transport metadata is preserved, VLC diagnostics identify safe media context and transport type, `EncounteredError` participates in bounded recovery, stale/duplicate/intentional actions remain guarded, and the final implementation passes the complete non-presentation local corpus plus hosted Windows packaged gates.

This is **not a commercial-readiness claim**. The final decision is:

> **RELEASE DECISION: IMPLEMENTED AND VALIDATED AT THE SYNTHETIC + HOSTED-WINDOWS APPLICATION BOUNDARY; PARTIAL FOR PROVIDER-SPECIFIC MEDIA BEHAVIOR; DO NOT CLAIM UNIVERSAL OR POPULATED-REAL-PROVIDER PLAYBACK ACCEPTANCE.**

No release tag was modified, no force push was used, no empty commit was created, and no external implementation was copied.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player "SamoTech IPTV Player repository"

[2]: https://github.com/4gray/iptvnator "IPTVnator repository"

[3]: https://github.com/4gray/iptvnator/blob/master/docs/architecture/embedded-inline-playback.md "IPTVnator embedded inline playback architecture"

[4]: https://github.com/4gray/iptvnator/blob/master/libs/ui/playback/src/lib/web-player-view/web-player-recovery-policy.ts "IPTVnator web-player recovery policy"

[5]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32156943241 "SamoTech Phase 3 hosted Windows validation run"

[6]: https://github.com/kiddac/XStreamity "KiddaC XStreamity repository"

[7]: https://github.com/kiddac/EStalker "KiddaC EStalker repository"

[8]: https://wiki.videolan.org/VLC_command-line_help/ "VideoLAN VLC command-line help"

[9]: https://images.videolan.org/vlc/features.html "VideoLAN VLC features"

[10]: https://images.videolan.org/vlc/libvlc.html "VideoLAN libVLC overview"

[11]: https://python-vlc.readthedocs.io/en/latest/ "python-vlc documentation"

[12]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/application/dtos/playback.py "SamoTech playback DTOs"

[13]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "SamoTech VLC player adapter"

[14]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/providers/xtream_request_builder.py "SamoTech Xtream request builder"

[15]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/protocol_profile.py "SamoTech MAG protocol profiles"

[16]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/session.py "SamoTech MAG session lifecycle"

[17]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32155782731 "SamoTech Phase 3 hosted Windows validation run for the first implementation commit"

[18]: https://github.com/4gray/iptvnator/blob/master/libs/ui/playback/src/lib/web-player-view/playback-recovery-session.ts "IPTVnator playback recovery session"

[19]: https://github.com/4gray/iptvnator/blob/master/libs/ui/playback/src/lib/web-player-view/electron-stream-headers.service.ts "IPTVnator scoped stream headers service"

[20]: https://github.com/4gray/iptvnator/blob/master/libs/portal/xtream/data-access/src/lib/services/xtream-url.service.ts "IPTVnator Xtream URL service"

[21]: https://github.com/4gray/iptvnator/blob/master/libs/shared/m3u-utils/src/lib/playlist.utils.ts "IPTVnator M3U playlist utilities"

[22]: https://github.com/4gray/iptvnator/blob/master/libs/shared/interfaces/src/lib/portal-playback.interface.ts "IPTVnator portal playback interface"

[23]: https://github.com/4gray/iptvnator/blob/master/libs/shared/interfaces/src/lib/parsed-playlist.interface.ts "IPTVnator parsed playlist interface"

[24]: https://github.com/SamoTech/samotech-iptv-player/blob/main/docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md "SamoTech protocol and playback architecture"

[25]: https://github.com/SamoTech/samotech-iptv-player/blob/main/build/PHASE2_FULL_TEST_BLOCKER.md "SamoTech full-suite Qt collection blocker"

[26]: https://github.com/SamoTech/samotech-iptv-player/blob/main/PROJECT_STATUS.md "SamoTech project status and limitations"
