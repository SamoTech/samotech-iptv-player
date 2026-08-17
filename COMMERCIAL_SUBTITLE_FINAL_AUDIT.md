# SamoTech Commercial Provider Experience plus Player Subtitle and Playback Enhancement — Final Audit

**Date:** 2026-08-17  
**Author:** Manus AI  
**Repository:** `SamoTech/samotech-iptv-player`  
**Audit scope:** Authoritative Commercial Provider Experience plus Player Subtitle and Playback Enhancement specification  
**Evidence vocabulary:** **IMPLEMENTED**, **VERIFIED**, **NOT IMPLEMENTED**, **NOT EXECUTED**, **BLOCKED BY EVIDENCE**, and **FUTURE WORK** are used literally. Synthetic, Linux/offscreen, or source-level evidence is not promoted to Windows-native or populated-provider acceptance.

> **Executive classification:** Provider Health, non-blocking onboarding, unified local search with content-type filters, local SRT/ASS/SSA/VTT subtitle loading, subtitle-slave removal, bounded subtitle delay, and session-safe subtitle state management are **IMPLEMENTED and deterministically VERIFIED** within the preserved provider, application, PlayerPort, qasync, and libVLC architecture. Catch-up/archive is **NOT IMPLEMENTED** because no current provider advertises a verified capability. Windows-native VLC validation and populated authorized-provider acceptance are **NOT EXECUTED** in this Linux environment.

## 1. Task overview and authoritative scope

The task was to read the supplied specification completely, derive and execute its dependency-ordered Todo List, inspect before modifying, preserve existing work, verify each implementation, document exact blockers, create logical commits, push normally to `origin/main`, and deliver this report as the single final audit artifact.

The scope explicitly prohibited provider-architecture rewrites, MAG/Xtream/M3U replacement, changes to bounded Live EOF recovery, new libVLC ownership, qasync replacement, UI access to libVLC or credentials, UI construction of provider URLs, guessed capabilities, fake subtitle attachment, fake subtitle delay, and claims that synthetic fixtures establish real provider compatibility.

## 2. Baseline and starting repository state

The repository was already on the Player 3 revision at the start of this continuation. The existing architecture contained provider-specific infrastructure adapters, canonical domain records, application use cases and ports, provider-scoped history/resume behavior, typed `ResolvedPlayback`, a shared libVLC player, qasync lifecycle, native PlayerShell probes, and bounded Live EOF recovery.

The implementation therefore extended existing seams rather than creating a parallel provider or playback stack. The environment-generated `uv.lock` was removed before commit and was not included in the delivery.

## 3. Read-only audit and dependency-ordered Todo List

The complete specification was converted to `/tmp/samotech_commercial_subtitle_todo.md`. The dependency order was: repository and architecture audit; Provider Health and onboarding; capability/state propagation; unified search; Series and resume audit; EPG/player/catch-up audit; local subtitle validation and PlayerPort extension; verified libVLC subtitle APIs; session safety; focused regression coverage; quality gates and performance; documentation; final report; logical commits; normal push; and synchronized-origin verification.

The audit confirmed that provider credentials remain in the keyring boundary, provider URL construction remains in infrastructure, application code consumes canonical records and typed ports, PlayerShell delegates playback through existing application/player seams, and libVLC remains the sole decoder/backend.

## 4. Provider architecture preservation

The delivery preserves the existing M3U, Xtream, MAG/Stalker, provider registry, resolver, canonical DTO, application use-case, SQLite, keyring, qasync, shared-player, and `ResolvedPlayback` boundaries. No provider adapter was rewritten and no provider capability was added solely because a protocol or public reference might support it.

The desktop UI does not import libVLC, create provider URLs, read credentials, or bypass `PlayerPort`. Local subtitle files remain a presentation/application input and never cross a provider or upload boundary.

## 5. Provider Health use case

`src/samotech_iptv/application/use_cases/check_provider_health.py` adds the synchronous `CheckProviderHealth` use case. It reports a safe `ProviderHealth` snapshot from declared capability data and adapter authentication state without loading a full catalogue, returning provider exception text, or exposing credentials.

`ProviderHealthStatus` distinguishes connected, unauthenticated, unknown, and error classifications. The `ProviderMetadata.health` field is optional, preserving backward-compatible provider metadata construction and safe base formatting when no health check has yet run.

**Classification:** **IMPLEMENTED / VERIFIED** by focused application tests and provider-management presentation tests.

## 6. Non-blocking post-save onboarding

The main window accepts an optional `CheckProviderHealth` dependency through desktop bootstrap and production composition. After a successful provider save, `_onboard_provider()` schedules the health check through the existing Qt/qasync task ownership path and reports generic readiness or failure feedback.

The onboarding path is intentionally bounded: Save → registered provider state → safe health check → capability/health summary → Ready or generic error. It does not block the Qt event loop or trigger full catalogue loading. Provider list refresh and selector/state propagation continue through existing registration boundaries.

**Classification:** **IMPLEMENTED / VERIFIED**. A real provider health result was not claimed because populated authorized-provider acceptance was not executed.

## 7. Conservative capability detection and state propagation

Health summaries use only declared capabilities and adapter authentication state. Unknown is not converted to unsupported, and unsupported is not converted to available. The list dialog renders a compact capability and health summary without secret values.

Manual Add, Smart Import, provider persistence, registry refresh, selector state, and provider switching remain on the existing paths. No restart requirement or alternate provider store was introduced. Existing stale-provider and stale-result protections remain in force.

**Classification:** **IMPLEMENTED / VERIFIED** for deterministic state and presentation coverage; real provider capability correctness remains **NOT EXECUTED**.

## 8. Unified search and content-type filters

`PlayerShell` now exposes an `All`, `Live`, `Movies`, `Series`, and `Episodes` filter for the local global search surface. Search operates on explicitly loaded local channel/catalogue/episode structures and does not create provider requests or a second cache.

Episode search includes title, plot, season number, and episode number. Result labels identify the content type and preserve the existing selection/activation flow. The native probe verifies a filtered `EPISODES · Pilot` result and the All-filter behavior after the Series → Season → Episode path is loaded.

**Classification:** **IMPLEMENTED / VERIFIED** by native PlayerShell assertions and isolated presentation regression coverage.

## 9. VOD/Series resume and Continue Watching boundary

The existing provider-scoped history/resume implementation remains authoritative. Movie and Episode progress uses stable provider/content identity and existing typed history fields; incomplete records can restore bounded progress through existing contracts. The delivery did not invent a new server-side resume protocol or a fake Continue Watching source.

Series remains a container. The existing Series → Season → Episode navigation, metadata presentation, provider-scoped identity, and playback handoff remain intact. No auto-play, guessed next-episode behavior, or new provider URL path was introduced.

**Classification:** **IMPLEMENTED / VERIFIED within existing bounded contracts**. Populated-provider resume acceptance is **NOT EXECUTED**.

## 10. EPG and live presentation audit

Existing EPG/live presentation, backend state rendering, playback controls, keyboard shortcuts, and bounded Live EOF recovery were audited and preserved. No change was made to Live EOF recovery, provider retry policy, decoder options, qasync lifecycle, or live stream resolution.

EPG remains provider/canonical-data driven and non-blocking within its existing scope. Catch-up linkage is not inferred from EPG timestamps, and no archive action was added without a provider-neutral contract.

**Classification:** Existing supported behavior **VERIFIED** by the focused player/EPG/VLC regression groups; catch-up linkage is **NOT IMPLEMENTED**.

## 11. Commercial player-control audit

The existing PlayerShell controls for play/pause, stop, timeline/seek, volume/mute, fullscreen, position/duration, buffering/error state, track menus, episode navigation, and overlay behavior remain contract-driven. The UI continues to use the injected player/application boundaries.

The delivery adds only subtitle operations that are backed by actual player capabilities. No UI-side libVLC calls, second player instance, fake track list, or unsupported transport behavior was added.

**Classification:** **IMPLEMENTED / VERIFIED** within the existing player contract and isolated Qt/native probe boundaries.

## 12. Local subtitle file validation

`src/samotech_iptv/application/local_subtitles.py` adds `inspect_local_subtitle()` and a `LocalSubtitleFile` value object. Validation is local and bounded by file existence, regular-file checks, size limits, UTF-8-safe decoding, extension allow-listing, timestamp/event structure, ASS/SSA header/event structure, and VTT header/cue structure.

Malformed, empty, unsupported, inaccessible, and oversized files are rejected without logging their contents. Arabic, RTL, mixed text, and other non-ASCII payloads remain file-local; validation does not normalize or persist subtitle content.

**Classification:** **IMPLEMENTED / VERIFIED** by focused SRT, ASS, SSA, VTT, UTF-8, malformed, missing, unsupported, and huge-file tests.

## 13. Local subtitle attachment

The PlayerPort now exposes optional capability-gated methods for `attach_local_subtitle()` and `clear_local_subtitles()`. The VLC adapter attaches a validated local file through the verified libVLC `MediaPlayer.add_slave` API without restarting the current media.

PlayerShell uses a file picker and delegates the selected file through the application/player boundary. It never uploads, persists, logs, or executes the file, and it does not construct provider URLs.

**Classification:** **IMPLEMENTED / VERIFIED** with fake-backed PlayerPort and VLC adapter tests. Native runtime attachment on Windows was **NOT EXECUTED**.

## 14. Subtitle-slave removal and source separation

The VLC adapter uses the verified libVLC `Media.slaves_clear` API to remove local subtitle slaves. This is separate from embedded/provider subtitle-track selection: the existing subtitle-track menu remains a player-track concern, while local subtitle files are explicit external sources.

Replacement and removal are guarded so stale local subtitle actions cannot affect a later media generation. No fake removal state is reported as successful when the player capability is absent.

**Classification:** **IMPLEMENTED / VERIFIED** by adapter tests covering `add_slave`, `slaves_clear`, replacement, and safe unsupported behavior.

## 15. Subtitle delay controls

The PlayerPort exposes `get_subtitle_delay_ms()` and `set_subtitle_delay_ms()`. The VLC adapter maps these methods to verified libVLC `video_get_spu_delay` and `video_set_spu_delay` APIs.

PlayerShell provides bounded delay actions through the subtitle menu. Values are clamped to a safe ±60,000 millisecond range, and controls are shown only when the injected player advertises `subtitle_delay` capability.

**Classification:** **IMPLEMENTED / VERIFIED** by bounded adapter tests and capability-gated UI code. Native libVLC delay behavior on Windows was **NOT EXECUTED**.

## 16. Subtitle session and generation safety

PlayerShell maintains a subtitle session token and invalidates it on media/provider/channel/episode changes, stop, and shutdown paths. Before attachment, the selected local subtitle operation verifies the current session/media generation and current media identity.

The VLC adapter also tracks the current resolved media and rejects attachment when no matching media is active. These guards prevent stale asynchronous work from attaching a subtitle to another movie, episode, live channel, provider, or media generation.

**Classification:** **IMPLEMENTED / VERIFIED** by fake-backed generation-safe attachment coverage and native stale-provider/player-shell probes.

## 17. Focused regression coverage

New focused coverage includes three Provider Health tests, four local subtitle test groups, VLC adapter tests for subtitle attachment/removal/delay and generation safety, and native PlayerShell assertions for content filters and episode search. Existing provider-management, main-window, PlayerShell, EPG, history/resume, playback, and VLC tests were re-run.

The broad non-presentation corpus collected **725 tests** and passed with coverage output. The presentation corpus was executed one module per process because combined offscreen Qt teardown is a known environment limitation; every isolated presentation module passed, with matrix status 0.

## 18. Native and performance probes

`tests/player_shell_native_probe.py` passed with all reported probe categories, including stale identity, provider selection, stale playback protection, content identity/local search, Series/search stale-provider protection, keyboard accessibility, artwork/provider invalidation, and the new Episode-filter search assertions.

`tests/player_shell_performance_probe.py` passed across dynamic catalogue sizes through 100,000 records. At 100,000 synthetic Series records, model replacement was 13.427 ms, search rendering was 96.111 ms, no-match search was 93.992 ms, and clearing search was 5.771 ms in the captured run. These are local-model measurements, not network or decoder benchmarks.

## 19. Quality-gate matrix

| Gate | Result | Evidence |
|---|---|---|
| Black | **PASS** | `339 files would be left unchanged.` |
| Ruff | **PASS** | `All checks passed!` |
| mypy | **PASS** | `Success: no issues found in 218 source files` |
| Broad non-presentation pytest | **PASS** | 725 collected and passing in the coverage run; measured total coverage 61% for that deliberately non-Qt invocation |
| Isolated presentation pytest matrix | **PASS** | Every `tests/test_presentation_*.py` module passed; `MATRIX_STATUS=0` |
| Native PlayerShell probe | **PASS / LIMITED** | Linux/offscreen exit code 0; all categories reported PASS |
| PlayerShell performance probe | **PASS** | Dynamic sizes through 100,000 records |
| Native VLC lifecycle probe | **SKIP / WINDOWS-ONLY** | `native_vlc_lifecycle=SKIP reason=windows_required` |
| VLC track-shape probe | **BLOCKED BY ENVIRONMENT** | Native binding failed with `NameError: no function 'libvlc_new'`; no product claim was inferred |
| Credential scan | **PASS** | 455 tracked/worktree files scanned; zero authorized credential literal violations |
| `git diff --check` | **PASS** | No whitespace errors before commit |

Coverage is reported as an evidence metric rather than a release threshold. The aggregate percentage is intentionally affected by excluding Qt-heavy modules from the broad run and is not hidden.

## 20. Security review

The security scan inspected tracked and non-ignored worktree files for the authorized Xtream username/password literals and reported zero violations across 455 files. No credential values, tokenized URLs, cookies, authorization headers, raw subtitle contents, or captured provider payloads were added to committed files.

Local subtitle handling is explicitly local-only. Subtitle content is not uploaded, logged, persisted, executed, or included in diagnostics. User-facing health and onboarding messages remain credential-free and do not render raw provider exception text.

## 21. Platform and native-runtime limitations

The verification environment is Linux with offscreen Qt. The PlayerShell native probe and isolated presentation matrix run successfully. The Windows-only VLC lifecycle probe correctly reports `SKIP reason=windows_required`.

The optional VLC track-shape probe is not a passing product gate in this environment because the installed Python binding could not resolve native `libvlc_new`. This is recorded as an environment blocker, not worked around by faking libVLC behavior. Native Windows subtitle attachment, subtitle delay, slave removal, and real stream playback remain **NOT EXECUTED**.

## 22. Real-provider acceptance disposition

Populated authorized Xtream acceptance was **NOT EXECUTED** in this delivery. No provider counts, subscription metadata, credentials, raw payloads, stream URLs, or runtime account details are included in this report.

Synthetic adapter fixtures, local Qt probes, and source-level libVLC API verification establish readiness and boundary behavior only. A future authorized run must record aggregate-only results for health, capability detection, catalogue loading, playback, subtitles, and delay without storing secrets or raw payloads.

## 23. Explicit deferred, blocked, and not-executed scope

| Scope item | Classification | Exact reason |
|---|---|---|
| Catch-up/archive | **NOT IMPLEMENTED** | No current provider advertises `ProviderCapability.CATCHUP`; no provider-neutral archive contract is proven. |
| Windows-native VLC lifecycle and subtitle runtime | **NOT EXECUTED** | Current execution environment is Linux; the lifecycle probe is Windows-gated. |
| VLC track-shape native probe | **BLOCKED BY ENVIRONMENT** | Native binding cannot resolve `libvlc_new` in the sandbox. |
| Populated authorized Xtream acceptance | **NOT EXECUTED** | No real-provider acceptance run was performed in this delivery. |
| Real provider subtitle interoperability | **NOT EXECUTED** | Requires a populated authorized provider and native player runtime. |
| MAG VOD/Series/Episodes | **BLOCKED BY EVIDENCE / NOT EXECUTED** | Existing authorized evidence does not establish a compatible non-live contract. |
| Remote/tokenized XMLTV caching and scheduling | **FUTURE WORK** | Existing XMLTV scope remains local/file and manually refreshed. |

No deferred item was represented as implemented because an enum, interface, synthetic fixture, or public protocol reference exists.

## 24. Documentation reconciliation

`README.md` now documents Provider Health, non-blocking onboarding, local content-type search, supported subtitle formats, local-only subtitle security, session safety, subtitle delay/removal, and explicit acceptance limitations. `CHANGELOG.md` records the dated implementation increment. `PROJECT_STATUS.md` records the current capability matrix and evidence classifications.

This report is the single delivery audit. Repository-internal references are listed in Section 26; no external provider data is cited or retained.

## 25. Files changed and logical commits

The implementation changes are concentrated in Provider Health DTO/use-case/composition and provider-list/main-window wiring; PlayerShell unified search and subtitle session/UI actions; PlayerPort/player capability DTOs; local subtitle validation; and the VLC adapter’s real subtitle APIs. Regression coverage includes application, adapter, and native PlayerShell tests.

The logical commits created before this report are:

| Order | Commit | Message |
|---:|---|---|
| 1 | `563a145` | `feat: add credential-free provider health check and non-blocking onboarding` |
| 2 | `9aef718` | `feat: add unified search content-type filters and episode search` |
| 3 | `f8bffce` | `feat: add local subtitle loading, delay controls, and session-safe subtitle management` |
| 4 | `4692d54` | `test: add provider health, local subtitle, and VLC subtitle regression coverage` |
| 5 | `a519330` | `docs: document commercial provider experience and subtitle enhancement` |
| 6 | `0d77d38` | `docs: write COMMERCIAL_SUBTITLE_FINAL_AUDIT.md` |
| 7 | Final documentation reconciliation | Corrected post-push synchronization wording after the report commit; no implementation changes. |

No force-push or history rewrite is permitted. The report was created in commit `0d77d38` and then reconciled in a normal follow-up documentation commit so the checked-in text reflects the final verification sequence.

## 26. Final status and evidence index

Implementation, deterministic tests, isolated Qt validation, performance, security review, documentation updates, seven logical commits including this final wording reconciliation, normal pushes, and post-push synchronization verification are complete. The final verification recorded equal local `HEAD` and `origin/main` revisions with an empty worktree after removing the regenerated environment `uv.lock` artifact.

The final classification is **READY FOR HANDOFF WITH EXPLICIT ACCEPTANCE LIMITATIONS**: the requested commercial provider-health, onboarding, search, subtitle, delay, removal, and session-safety work is implemented and verified within the available architecture and environment. Catch-up/archive is not implemented. Windows-native validation, native VLC track-shape validation, and populated authorized-provider acceptance are not executed or environment-blocked as described above.

### References and evidence index

1. [README.md](README.md) — product scope, security model, architecture, and current commercial/subtitle summary.
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) — authoritative current capability and limitation matrix.
3. [CHANGELOG.md](CHANGELOG.md) — dated implementation history.
4. [ARCHITECTURE.md](ARCHITECTURE.md) — dependency direction and provider/player boundaries.
5. [SECURITY.md](SECURITY.md) — repository security policy.
6. [tests/player_shell_native_probe.py](tests/player_shell_native_probe.py) — native offscreen PlayerShell and search-filter probe.
7. [tests/player_shell_performance_probe.py](tests/player_shell_performance_probe.py) — large-catalogue performance probe.
8. [tests/vlc_native_lifecycle_probe.py](tests/vlc_native_lifecycle_probe.py) — Windows-classified native VLC lifecycle probe.
9. [tests/test_application_check_provider_health.py](tests/test_application_check_provider_health.py) — Provider Health regression coverage.
10. [tests/test_application_local_subtitles.py](tests/test_application_local_subtitles.py) — local subtitle validation coverage.
11. [tests/test_infra_vlc_player_adapter.py](tests/test_infra_vlc_player_adapter.py) — real VLC API boundary and generation-safe subtitle tests.
12. [src/samotech_iptv/application/local_subtitles.py](src/samotech_iptv/application/local_subtitles.py) — local-only subtitle inspection boundary.
13. [src/samotech_iptv/application/use_cases/check_provider_health.py](src/samotech_iptv/application/use_cases/check_provider_health.py) — credential-free health use case.
14. [src/samotech_iptv/infrastructure/player/vlc_player_adapter.py](src/samotech_iptv/infrastructure/player/vlc_player_adapter.py) — libVLC subtitle attachment, removal, and delay implementation.
