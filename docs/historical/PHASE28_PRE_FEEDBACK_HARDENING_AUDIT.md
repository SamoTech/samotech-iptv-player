# Phase 28 — Pre-Feedback Hardening Audit

**Repository:** `SamoTech/samotech-iptv-player`
**Wave 5 implementation commit:** `2b7ee0151d04a7cea1518ddcdb4a6ff22d993dea`
**Current public release preserved:** [`v0.1.6`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.6)
**Windows validation:** [run 32347896794](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32347896794) — **PASS**

## 1. Final Status

> **FINAL DECISION: READY FOR CONTROLLED REDDIT FEEDBACK COLLECTION.** Wave 5 hardened the observed first-run and recovery journeys, preserved the v0.1.6 public-testing release boundaries, and passed required local and hosted Windows validations. No new release, tag, version increment, release asset, workflow permission, or README badge-block modification was made.

The project is ready to gather structured public-testing evidence through the existing feedback path and the new developer intake checklist. It is **not** certified as universally compatible with every IPTV provider, codec, container, device, MAG/Stalker portal, platform, or multi-monitor environment. [1] [2]

| Decision area | Status |
|---|---|
| v0.1.6 release identity and public-testing classification | **PRESERVED** |
| Low-risk user-journey hardening | **COMPLETE** |
| Deterministic and static validation | **PASS** |
| Hosted Windows package validation | **PASS** |
| Safe Reddit-feedback intake process | **COMPLETE** |
| New release/publication | **NOT AUTHORIZED AND NOT CREATED** |
| Real provider and decoded-media compatibility | **NOT VERIFIED** |

## 2. Completed Tasks

| Workstream | Completed outcome |
|---|---|
| Forensic baseline | Captured v0.1.6 release identity, release/tag protections, `HEAD == origin/main` at baseline, workflow state, architecture boundaries, diagnostic model, launcher, and byte-exact README badge digest. [1] |
| User-journey audit | Audited first-run, provider setup, empty/error states, playback controls, fullscreen, keyboard, search, large data, EPG, favorites/history, settings, diagnostics, launcher, logging, provider/media boundaries, and capability truth. [2] |
| Playback recovery UX | Added a disabled-until-needed **Retry** control that reuses the established typed live-playback path; no second recovery system was created. |
| Safe playback errors | Added bounded user-facing playback messages for rejected access, network timeout, unavailable source, unsupported media, and generic failure. Untrusted provider detail is never echoed to the UI. |
| EPG friction | Normal PlayerShell EPG launch now carries the selected live channel context, avoiding normal-user entry of provider/channel IDs. The advanced dialog retains guarded fallback fields and actionable no-selection/error text. |
| Favorites usability | Replaced raw favorite/provider/item identifier display and manual typed-ID removal with safe numbered item-type summaries and selected-item removal. |
| History usability | Replaced raw history/item IDs and opaque ISO-first summaries with safe media-type, continuation/completion, duration, and last-watched copy. |
| Source/setup audit | Reconfirmed existing M3U file/URL, Xtream masked credentials, MAG/Stalker constraints, and Smart Import protocol-specific input behavior. No provider protocol behavior was invented. |
| Documentation and feedback readiness | Added `docs/REDDIT_FEEDBACK_INTAKE_CHECKLIST.md` with privacy exclusions, safe diagnostics, safe debug-log handling, triage labels, engineering decision rules, and known limits. |

## 3. Verification Results

| Gate | Result | Evidence |
|---|---|---|
| Retry, safe error mapping, selected-channel EPG, Favorites, History, and PlayerShell focused tests | **PASS** | 16 focused tests passed after implementation and regression correction. |
| Provider setup, Smart Import, diagnostics, capability, libVLC adapter, and large-data focused suite | **PASS** | The selected functional suite passed, including the existing 10,000-item large-data probe. |
| Complete non-presentation corpus | **PASS** | All non-presentation test modules passed; existing aiohttp bare-function deprecation warnings remained. |
| All presentation modules in isolated Qt processes | **PASS** | 19 `test_presentation*.py` files passed individually with `QT_QPA_PLATFORM=offscreen`. |
| Complete local pytest collection | **BLOCKED_ENVIRONMENT** | Exit 139 while collecting `test_presentation_smart_import_dialog.py` through PySide6/shiboken. The full-suite fault is recorded; no test was silently skipped. |
| Ruff | **PASS** | `src`, `tests`, `providers`, and `scripts` clean. |
| Black | **PASS** | 385 files unchanged. |
| MyPy | **PASS** | 225 source files, no issues. |
| Bandit production scan | **PASS** | No high/medium production finding; historic scoped comments/`nosec` warning noise remains. |
| Credential/redaction scan | **PASS** | No added credential-bearing URL, private key, authorization, cookie, or token assignment in production diff. New tests specifically prove private failure detail is not displayed. |
| Protected-boundary checks | **PASS** | README badge-block digest remains `d6310d733baae10823f9a84f2bb7ad157706930d993f4b26d78eb534d7da810d`; no version, release, asset, or workflow permission change. |
| Windows Portable EXE workflow | **PASS** | Hosted build passed pinned VLC preparation, Ruff, Black, MyPy, Windows non-Qt tests, native VLC lifecycle, EXE build, packaged VLC/Qt smoke, optional debug-launcher smoke, sanitized PATH/CWD execution, artifact audit, checksum, metadata, and artifact upload. [3] |

## 4. Changes Made

The changed behavior remains within the existing Python, PySide6, and libVLC architecture. The implementation maps user-facing failure information at the presentation boundary and reuses `PlayerShell.play_channel` for Retry. It does not modify provider adapters, protocol handling, VLC lifecycle ownership, media pipeline selection, secret storage, or release automation.

The EPG improvement passes selected `ChannelDTO` context to the existing EPG dialog, while preserving the advanced manual fallback. Favorites and History remain backed by their same application use cases and persistence records; only their presentation rendering/removal selection mechanics changed. This preserves the principle that opaque record identities stay internal rather than becoming normal-user workflow requirements.

## 5. Blocked Items and Exact Reasons

| ID | Classification | Exact reason |
|---|---|---|
| B-01 | **BLOCKED_ENVIRONMENT** | Linux monolithic pytest exits 139 during PySide6/shiboken collection/import of `test_presentation_smart_import_dialog.py`. Isolated presentation modules passed, and the hosted Windows workflow passed. |
| B-02 | **BLOCKED_ENVIRONMENT** | The Linux sandbox has no `libvlc.so`, `libvlccore.so`, or VLC executable. It cannot prove decoded IPTV frames, audio, codec/container behavior, or actual HLS media continuity. |
| B-03 | **BLOCKED_EXTERNAL** | No newly authorized real M3U, Xtream, or MAG/Stalker provider fixture was supplied for catalogue, authentication, temporary URL, session, or media acceptance. |
| B-04 | **WINDOWS-ONLY VALIDATION GAP** | The hosted pipeline validates Windows package startup, full path/PATH/CWD cases, bundled VLC/Qt, and launcher behavior, but it cannot substitute for manual multi-monitor, taskbar, focus-restoration, assistive-technology, or long-session observation. |
| B-05 | **SCOPED ENVIRONMENT FINDING** | Dependency audit continues to report global `pypdf` and `xhtml2pdf` vulnerabilities not declared by this repository. The project-controlled Wheel finding was remediated in Wave 4. |

## 6. Remaining Actions

The next activity is controlled feedback collection, not speculative media/protocol work. Developers should use the new checklist to request only safe reproduction steps, version/platform context, source category, content category, observed behavior, copied safe diagnostics, and confirmed-redacted debug output. Every report should be triaged before code changes, and any P0/P1 fix must repeat the established test, quality, security, Windows packaging, and release process. [4]

The local PySide6 collection fault should be isolated as an environment-specific test-infrastructure task. Real provider behavior should be added only with new authorized fixtures and sanitized evidence. Multi-monitor/focus/fullscreen, actual decoded-media behavior, advanced MAG/Stalker flow, provider session refresh, non-HTTP transport, codec coverage, and platform-client expansion remain independent milestones.

## 7. Release and Repository Integrity

Package version remains `0.1.6`. The historical `v0.1.5` and `v0.1.6` tags/releases and their published assets remain untouched. The README badge block remains byte-identical, no force push/history rewrite occurred, and no GitHub Actions permission or release condition was weakened.

The Wave 5 candidate was committed only after the relevant deterministic gates passed, then verified by the required main-branch Windows Portable EXE workflow. The final documentation follows as an evidence record only; it is not a release action.

## References

[1]: [`docs/evidence/WAVE5_BASELINE.md`](../evidence/WAVE5_BASELINE.md)
[2]: [`docs/evidence/WAVE5_USER_JOURNEY_AUDIT.md`](../evidence/WAVE5_USER_JOURNEY_AUDIT.md)
[3]: [Windows Portable EXE workflow run 32347896794](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32347896794)
[4]: [`docs/REDDIT_FEEDBACK_INTAKE_CHECKLIST.md`](../testing/REDDIT_FEEDBACK_INTAKE_CHECKLIST.md)
