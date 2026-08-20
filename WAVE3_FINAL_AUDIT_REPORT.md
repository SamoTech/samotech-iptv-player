# Wave 3 Full IPTV Media Player Engine — Final Audit Report

**Repository:** `SamoTech/samotech-iptv-player`  
**Implementation commit validated on Windows:** `b1dd16090fc9de1e8a788af55b78b319d1401363`  
**Windows validation:** [Run 32332197058](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32332197058) — **PASS**  
**Release action:** **None.** No tag, release, version, published asset, README badge, or GitHub Actions permission change was made.

## 1. Executive Conclusion

Wave 3 was executed as an evidence-first extension of the existing Python/PySide6/libVLC architecture. The repository already contained a single lifecycle-owned playback path, provider-neutral resolved-playback boundary, typed live/VOD recovery distinctions, and Windows packaged-VLC validation. The implementation therefore did **not** introduce Flutter/media-kit, hls.js, MPV, a custom codec pipeline, an external VLC process, a proxy, or a second recovery system. [1] [2]

The completed Wave 3 code adds a typed, optional account-expiration/trial model and a four-state provider-capability truth model. The existing provider-management surface now distinguishes **supported**, **not supported**, **not available**, and **not verified** instead of treating all false booleans as the same result. Xtream translation preserves explicitly provider-supplied trial information without inventing an expiration value. [3] [4]

> **FINAL CLASSIFICATION: B — architecture, deterministic controls, security gates, and Windows packaging are accepted; real decoded-media and authorized-provider acceptance remain blocked.**

This is not a new release recommendation. It is a verified branch improvement with clearly bounded runtime evidence. Real provider playback continuity must remain a separate acceptance decision.

## 2. Completed Tasks

| Workstream | Completed result | Evidence |
|---|---|---|
| Repository forensic | Produced `WAVE3_REPOSITORY_FORENSIC.md` before implementation changes | Current source/tree, historic audits, protected-boundary review |
| Capability matrix | Produced provider/media/backend/platform evidence matrix with honest status states | `docs/evidence/WAVE3_CAPABILITY_MATRIX.md` |
| Provider account model | Added `AccountStatus`, `SubscriptionStatus`, `AccountExpiration`, trial flag, optional timezone, and explicit remaining/expired calculations | Domain model and tests |
| Xtream account translation | Preserves explicit `is_trial`; unknown/malformed values stay absent rather than inferred | Translator regression coverage |
| Capability truth model | Added `SUPPORTED`, `NOT_SUPPORTED`, `NOT_VERIFIED`, and `NOT_AVAILABLE` states alongside legacy booleans | DTO/use-case/provider-summary regressions |
| Provider UI | Displays safe capability-state text without exposing credentials, URLs, headers, tokens, or account secrets | Provider-management regression |
| Playback boundary audit | Confirmed existing `PlaybackResource → ResolvedPlayback → PlayerPort → VlcPlayerAdapter` lifecycle and URL redaction contract | Existing use-case and adapter tests |
| Backend decision | Retained the existing sole libVLC implementation; documented rejected incompatible alternatives | `PLAYBACK_BACKEND_DECISION.md` |
| Protocol evidence | Documented HLS, MPEG-TS, MP4/fMP4, Xtream, MAG, and non-HTTP transport states without false verified claims | `PLAYBACK_PROTOCOL_MATRIX.md` |
| Runtime probe | Ran existing sanitized public-HLS VOD probe and recorded its exact pre-open native-runtime blocker | `WAVE3_RUNTIME_PROBE_LOG.md` |
| Lifecycle/product audit | Audited buffering, live liveness, bounded recovery, switching, VOD/series, EPG, catch-up, UI, and diagnostics | `WAVE3_PLAYBACK_LIFECYCLE_AUDIT.md` |
| Validation manifest | Produced deterministic/static/runtime/platform result inventory | `WAVE3_TEST_MANIFEST.md` |

## 3. Verification Results

| Gate | Result | Notes |
|---|---|---|
| Focused account, Xtream translator, capability, and provider-management regressions | **PASS — 32 tests** | Provider-management test ran with `QT_QPA_PLATFORM=offscreen` |
| Complete non-presentation pytest corpus | **PASS** | Presentation files excluded only after the monolithic Qt collection blocker; existing aiohttp deprecation warnings remained |
| Monolithic local pytest | **ENVIRONMENTAL BLOCKER** | Exit 139 / PySide6 segmentation fault during collection of `test_presentation_smart_import_dialog.py`, including with offscreen Qt |
| Ruff | **PASS** | Repository-wide `src tests providers scripts` |
| Black | **PASS** | 373 files unchanged |
| MyPy | **PASS** | 221 source files, no issues |
| Bandit | **PASS** | No high/medium findings; comments and historic scoped `nosec` warnings only |
| Dependency audit | **PASS** | No known vulnerabilities; the local project distribution itself is not on PyPI and cannot be audited |
| Diff/protected-boundary scan | **PASS** | No README/version/workflow/release change; no credential indicator found in changed code |
| Controlled public HLS VOD probe | **ENVIRONMENTAL BLOCKER** | No local `libvlc.so`, `libvlccore.so`, VLC executable, or configured VLC runtime; initialization stopped before media open |
| Windows portable workflow | **PASS** | Native VLC lifecycle, Ruff, Black, MyPy, Windows non-Qt corpus, EXE build, packaged VLC/Qt smoke, sanitized PATH, artifact audit, checksum, metadata, and artifact upload all passed |

The passing Windows workflow validates the actual changed commit and confirms that Wave 3 did not break the established packaged-VLC execution path. It does not prove HLS decoded frames/audio or a commercial provider subscription flow. [5]

## 4. Changes Made

### Application and Domain Changes

The account domain now normalizes a finite account status and optional subscription status. It includes an `AccountExpiration` value with explicit-reference `remaining_at`, `is_expired_at`, `days_remaining_at`, and `hours_remaining_at` operations, so UI, diagnostics, and health logic can share time semantics without deriving values from playback. The existing `expires_at`, active/max connections, and safe-message fields remain compatible. [3]

The provider capability DTO now preserves existing navigation booleans while adding a structured truth state. The capability use case maps actual provider declarations to `SUPPORTED` or `NOT_SUPPORTED`; a resolver failure becomes `NOT_AVAILABLE`, never silently “unsupported.” Default metadata remains `NOT_VERIFIED`. The provider list renders these states safely, avoiding false operational claims. [4]

### Evidence and Documentation Changes

New Wave 3 forensic, capability, backend-decision, protocol, lifecycle, runtime-probe, and test-manifest files are committed. They map each requirement to current source evidence, deterministic evidence, blocked evidence, or unsupported scope. The reports do not substitute a parsed manifest, URL construction, package smoke, or test double for decoded-media proof.

## 5. Blocked Items and Exact Reasons

| ID | Severity | Classification | Exact blocker |
|---|---|---|---|
| B-01 | P1 | **BLOCKED_EXTERNAL** | No newly supplied authorized Xtream/MAG provider fixture exists. Historic provider acceptance remains blocked, so account/session/media behavior cannot be asserted against a real provider. |
| B-02 | P1 | **ENVIRONMENTAL BLOCKER** | The Linux sandbox has no libVLC runtime. The controlled HLS probe fails with `NameError` during adapter initialization before a media object opens; no HLS/media diagnosis can be drawn. |
| B-03 | P2 | **ENVIRONMENTAL BLOCKER** | Full local pytest crashes in PySide6 collection at `test_presentation_smart_import_dialog.py` with exit 139. Independent offscreen provider-management validation passed, and the Windows non-Qt corpus passed. |
| B-04 | P2 | **NOT VERIFIED** | No safe runtime telemetry currently proves HLS manifest/segment success, MPEG-TS demux, MP4/fMP4 decode, H.264/H.265/MPEG-2 selection, decoded frame, audio initialization, or sustained playback. |
| B-05 | P2 | **UNSUPPORTED** | RTSP/RTP/UDP/SRT/RTMP and MAG VOD/series/catch-up are not executable claims at the current HTTP(S)-only player boundary. |
| B-06 | P3 | **NOT VERIFIED** | macOS, Android, iOS, web, manual Windows multi-monitor/fullscreen, and assistive-technology runs are outside the repository/runtime available for this task. |

## 6. Remaining Actions

The next action must be an authorized Windows runtime session, not another speculative code change. Use the existing sanitized harness with a newly supplied authorized provider and capture only redacted identifiers, typed state transitions, timings, event classes, recovery counts, decoded-frame/audio observations if instrumentation can prove them, and no raw URL/credential material. This should test one live source and one VOD source. [6]

If that evidence demonstrates provider-specific media headers, cookies, tokens, temporary URL refresh, or MAG playback-session maintenance, add it as ephemeral typed `TransportMetadata` or a provider-owned session mechanism at the existing boundary. Do not infer it from a control-plane API response, copy Enigma2 service types, or forward all portal headers to libVLC. [2]

The full PySide6 collection segmentation fault should be isolated in a dedicated Linux test-environment task. It is not a justification to skip presentation tests: retain isolated offscreen/native probes and the hosted Windows corpus until the collection issue is fixed. Catch-up/archive, non-HTTP transport support, and multi-platform clients require explicit contracts and independent evidence before implementation.

## 7. Release Impact and Protections

`pyproject.toml` remains at version `0.1.5`. The existing `v0.1.5` tag/release, release assets/checksum, README badge block, repository history, and GitHub Actions permissions were preserved. The successful main-branch Windows workflow ran with tag/release validation and release-note generation skipped by its existing conditions; no new release was published. [5]

## 8. Final Status

| Dimension | Status |
|---|---|
| Repository architecture | **ACCEPTED** — one shared libVLC lifecycle retained |
| Account/capability control-plane extension | **ACCEPTED** — typed, optional, provider-evidence-backed |
| Provider UI truthfulness | **ACCEPTED** — safe state distinctions added |
| Deterministic regression/static/security validation | **ACCEPTED** |
| Windows package validation | **ACCEPTED** — run 32332197058 passed |
| Real decoded media evidence | **NOT VERIFIED** |
| Authorized provider end-to-end playback | **BLOCKED_EXTERNAL** |
| Release decision | **DO NOT RELEASE** pending authorized runtime acceptance |

## References

[1]: `WAVE3_REPOSITORY_FORENSIC.md` — actual repository architecture and missing-artifact baseline.  
[2]: `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` and `docs/evidence/PLAYBACK_BACKEND_DECISION.md` — provider/media boundary and backend decision.  
[3]: `src/samotech_iptv/domain/entities/account_info.py` and `tests/test_domain_provider_runtime_records.py` — typed optional account-expiration model.  
[4]: `src/samotech_iptv/application/dtos/provider.py`, `src/samotech_iptv/application/use_cases/load_provider_capabilities.py`, and `src/samotech_iptv/presentation/dialogs/provider_list_dialog.py` — four-state capability model and safe rendering.  
[5]: [Windows Portable EXE workflow run 32332197058](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32332197058) — final hosted validation.  
[6]: `docs/evidence/WAVE3_RUNTIME_PROBE_LOG.md` and `docs/evidence/WAVE3_TEST_MANIFEST.md` — runtime and environment evidence boundaries.
