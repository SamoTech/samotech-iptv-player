# Phase 27 — Real User UI/UX & Large Playlist Acceptance Audit

**Project:** SamoTech IPTV Player  
**Audit scope:** Real user-feedback investigation, targeted usability remediation, large-data acceptance, regression protection, and release impact  
**Implementation baseline validated:** `6c7d15f46b41b2b22ba2745cc722fb00c1cd817b`  
**Windows workflow:** [Run 32330586667](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32330586667) — **PASS**  
**Release action:** **None. No tag, release, asset, version, badge, or CI-gate change was made.**

## 1. Executive Summary

Phase 27 investigated the supplied real-user feedback as hypotheses rather than treating it as proof. The audit confirmed three high-value, low-risk issues: the M3U add flow exposed unnecessary provider-ID complexity; theme selection used a free-text field despite having only three legal values; and Xtream URLs that include a service subpath could lose that path during normalization and request construction. A fourth finding—ordinary settings navigation opening a separate dialog—was confirmed as a usability issue and remediated by adding a direct in-shell Settings page while preserving the dialog fallback for reduced shells and existing compatibility paths. [1] [2] [3]

The implementation did **not** change provider boundaries, libVLC, recovery behavior, credential storage, CI permissions, release logic, tags, or published assets. It added deterministic, local-only 10,000-item acceptance coverage for channels, movies, series, EPG entries, categories, cached search, M3U parsing, selection/scrolling, CPU, RSS, and process-thread counts. The implementation and existing behavior passed focused tests, the final local non-presentation corpus, static gates, dependency audit, Bandit, and the full Windows portable build/smoke pipeline. [4] [5]

> **Decision:** The Phase 27 code change is accepted for the current `main` branch. A new production release remains **not recommended** until real authorized-provider playback continuity is obtained, because Phase 25 and Phase 26 remain provider-validation blocked rather than because of a Phase 27 code failure. [6] [7]

| Finding class | P0 | P1 | P2 | P3 | Total |
|---|---:|---:|---:|---:|---:|
| **Confirmed defect** | 0 | 1 | 0 | 0 | 1 |
| **Confirmed usability issue** | 0 | 2 | 2 | 0 | 4 |
| **Not reproduced** | 0 | 0 | 1 | 0 | 1 |
| **Not tested / environmental blocker** | 0 | 0 | 0 | 5 | 5 |
| **Total classified findings** | **0** | **3** | **3** | **5** | **11** |

## 2. User Feedback Inventory

The audit evaluated the reported feedback across large playlist/EPG responsiveness, dialog-heavy navigation, direct Settings access, finite theme selection, M3U import complexity, and an Xtream provider that did not load. The feedback was not used as a source of credentials, endpoints, or provider evidence.

| ID | Feedback hypothesis | Classification | Evidence outcome | Implementation required |
|---|---|---|---|---|
| F-01 | Ordinary navigation causes too many top-level windows. | **USABILITY ISSUE / P1** | Multiple page entries still delegated to dialogs; Settings was the direct user-reported high-value case. | **Yes, targeted** |
| F-02 | Settings needs a second click and looks like a text-only theme field. | **USABILITY ISSUE / P1** | Confirmed: menu/top button opened a dialog and `ThemeSettingsDialog` used `QLineEdit`. | **Yes** |
| F-03 | M3U setup is more complex than URL or file selection. | **USABILITY ISSUE / P1** | Confirmed: form exposed Provider ID and did not provide Browse Local File. | **Yes** |
| F-04 | Xtream URL/user/password did not load. | **CONFIRMED DEFECT / P1** for subpath normalization; provider-specific failure itself **NOT REPRODUCED**. | A subpath could be dropped from `player_api.php` and stream URLs. No authorized Strong8k validation evidence existed. | **Yes, narrow fix** |
| F-05 | Large catalogues and EPG may make the UI unresponsive. | **NOT REPRODUCED / P2** within deterministic offscreen acceptance; real provider/network acceptance remains separate. | 10,000-item local measurement passed; parsing is the dominant measured operation. | **Coverage added; no blind optimization** |
| F-06 | Current errors may be overly technical. | **NOT REPRODUCED / P2** for the audited paths. | M3U and theme flows return safe user messages; translated provider errors remain redacted. | No architectural change |

## 3. Reproduction Results

The following reproduction record separates what was demonstrated from what remains unavailable.

| Finding | Reproduction steps | Expected behavior | Actual baseline behavior | Result |
|---|---|---|---|---|
| F-01 | Use navigation or the top Settings button. | Routine application navigation should remain in the primary window. | Settings invoked a separate `QDialog`. Other legacy library/EPG/provider entries still use dialog-backed views. | Confirmed usability issue |
| F-02 | Open Settings and inspect the editable value control. | Present System, Light, and Dark as finite choices. | A free-text `QLineEdit` accepted manually typed values. | Confirmed usability issue |
| F-03 | Open M3U provider setup. | Enter URL **or** browse local file, then load. | Provider ID was visible/required, with no browse button. | Confirmed usability issue |
| F-04 | Parse a URL such as `https://host:8443/iptv/player_api.php` and build an Xtream API/stream URL. | Keep `/iptv` and omit credentials from stored server URL. | Service path was lost; authority credentials could remain in the normalized server URL. | Confirmed defect |
| F-05 | Render/import deterministic 10,000-item fixtures in a real offscreen Qt process. | No provider call for cache search; model-based list rendering remains responsive. | All invariants passed; local measurements captured below. | Not reproduced in harness |

## 4. UI/UX Findings

The remediation intentionally follows the existing `PlayerShell` architecture instead of replacing dialogs globally. Settings is now an in-shell page with explicit System, Light, and Dark choices. This eliminates the second click for the direct Settings control while preserving a dialog fallback in `MainWindow` for reduced shells. [2] [3]

M3U setup now has a source-first shape: a playlist URL field, a **Browse Local File…** action, and a **Load Playlist** action. A deterministic `m3u-<safe-source>` identifier is generated only when no internal provider ID is supplied. The identifier remains an internal registration requirement; it is no longer front-loaded as a user task. Loading state disables conflicting actions, cancellation remains explicit, duplicate registration is translated to “This playlist has already been added,” and source text is retained after a duplicate or failure. [2]

## 5. Navigation Audit

The primary window already contains Home, Live TV, Movies, Series, Favorites, History, Search, Providers, and Settings navigation labels. The audit confirmed that several legacy library pages still launch dialog-backed content. Rather than broadly rewriting Favorites, History, EPG, and Providers without measured failure, Phase 27 fixed the exact direct Settings problem and recorded the remaining dialog-heavy views as a follow-up UX debt. [3]

| Navigation element | Baseline | Phase 27 disposition |
|---|---|---|
| Top-bar Settings | Opened dialog | **Direct in-shell page** |
| Menu Settings | Opened dialog | **Direct in-shell page** when PlayerShell exists; fallback retained |
| Theme control | Free text | **QComboBox: System / Light / Dark** |
| Favorites / History / Providers / EPG | Dialog-backed legacy pages | Retained; **P2/P3 follow-up**, not broadly rewritten |

## 6. Provider Setup Audit

Xtream, M3U, and MAG remain separate provider-specific boundaries. No generic form was introduced, and no real credentials were used. M3U now shows only appropriate playlist-source actions; Xtream and MAG retain their protocol-specific fields. Existing Smart Import behavior continues to mask passwords in previews and clear secret fields after registration. [2] [8]

## 7. M3U UX Audit

| Requirement | Result |
|---|---|
| Playlist URL | **PASS** — accessible URL/source field retained |
| Browse local M3U/M3U8 file | **PASS** — file chooser writes a `file:` URI locally |
| Load state | **PASS** — Load, Browse, and Cancel disable while registration is in progress |
| Error state | **PASS** — safe “Unable to register M3U provider” path |
| Success state | **PASS** — “M3U provider added” and existing callback behavior |
| Cancellation | **PASS** — explicit cancellation retained |
| Duplicate handling | **PASS** — user-facing duplicate message, source retained |
| Internal ID exposure | **PASS** — deterministic non-secret ID generated when absent |

## 8. Xtream Investigation

The provider pipeline was traced from provider configuration and Smart Import through credential handling, `XtreamRequestBuilder`, request construction, and the existing API-client response/error translation. The audit did not use the previously blocked provider credentials and did not bypass authentication or WAF restrictions. [1] [4]

The confirmed defect was limited and reproducible: `player_api.php` and stream URLs could be built at the authority root even when the configured provider endpoint used a service prefix such as `/iptv`. The fix preserves the normalized service path, strips known `get.php` and `player_api.php` endpoints, removes query data, and rebuilds `netloc` from hostname/port so authority credentials cannot remain in the stored server URL. Root-host behavior remains covered. [4] [8]

| Compatibility item | Result |
|---|---|
| HTTP/HTTPS | Supported by the existing URL contract; no change |
| Trailing slash | Normalized without a duplicate slash |
| `get.php` / `player_api.php` URL | Endpoint removed while service prefix is retained |
| Username/password in authority | Extracted for the detected provider; excluded from `server_url` |
| Subpath request/stream construction | **Fixed and tested** |
| HTML/WAF / HTTP failures | Existing error translation retained; no bypass implemented |
| Real authorized provider validation | **NOT TESTED** — previous provider endpoint was blocked; no new authorized source supplied |

## 9. Playback Controls Audit

Existing PlayerShell native-probe coverage passed after the change. The audit verified the controls currently supported by the application—play/pause, stop, previous/next channel selection, seek, volume, mute, progress/time status, fullscreen, Escape restoration, audio/subtitle capability states, and playback/error state labels. Unsupported controls are not added merely to imitate another player. [3] [9]

No playback or libVLC behavior was changed in this phase. The VLC adapter regression suite passed **48 tests**, including live-stall, VOD completion, and bounded-recovery coverage. [5]

## 10. Fullscreen Audit

The native PlayerShell probe revalidated focused fullscreen keyboard behavior. In particular, Space on a focused fullscreen button continues to fall through to native Qt button activation rather than being intercepted as a player shortcut; this preserves the Phase 24 acceptance condition. Escape, player-level keyboard controls, sidebar behavior, and focused controls remained covered in the offscreen native probe. [3]

Alt+Tab, minimize/restore, and multi-monitor behavior were **NOT TESTED** in this Linux offscreen audit. The final Windows workflow did pass generated-EXE Qt/application smoke and packaged-VLC smoke tests, but that is not a substitute for a manual multi-monitor usability session. [10]

## 11. Menu Audit

The Settings menu action now routes to `open_settings_page()` and uses the active PlayerShell when available. The legacy dialog fallback remains for test/reduced-shell compatibility. No menu labels were renamed, and no menu action was removed. The audit identified remaining dialog-backed menus as technical/UX debt rather than applying a broad unmeasured rewrite. [3]

## 12. Large Playlist Performance

The deterministic real-PySide6 probe exercised 10,000 channels, 10,000 movies, 10,000 series entries, 10,000 EPG entries, and 1,000 categories. The values below are local offscreen measurements, **not** a claim of equivalent real provider/network performance.

| Operation | Data size | Wall time | CPU time | Result |
|---|---:|---:|---:|---|
| PlayerShell startup | — | 96.278 ms | — | PASS |
| Initial live model render | 10,000 channels | 0.190 ms | 0.200 ms | PASS |
| Channel selection + scroll | row 5,000 | 322.044 ms | 321.863 ms | PASS |
| Category switch | 1,000 categories / 10 matching rows | 0.866 ms | 0.871 ms | PASS |
| Cached channel search | 10,000 channels / 1,000 hits | 0.937 ms | 0.942 ms | PASS; zero provider resolver/search calls |
| M3U parse | 10,000 entries | 565.286 ms | 565.128 ms | PASS; dominant measured local operation |
| Category selector population | 1,001 rows incl. All | 4.341 ms | — | PASS |
| Movies model render | 10,000 entries | 0.612 ms | 0.626 ms | PASS |
| Series model render | 10,000 entries | 0.659 ms | 0.672 ms | PASS |

Peak RSS changed from **65,624 KiB** to **117,604 KiB** during the Linux probe, a **51,980 KiB** increase. OS process threads remained 1 before and after, and Python active thread count was 1. Windows does not provide the POSIX `resource` module, so the probe records RSS as explicitly unsupported there while retaining all other invariants. [11]

## 13. EPG Performance

Rendering 10,000 locally constructed safe EPG rows took **48.057 ms** wall time and **48.055 ms** CPU time in the offscreen probe. The measurement validates the existing list rendering boundary; it does not validate remote XMLTV fetch duration, EPG parsing from a provider, or user-perceived scrolling on a Windows GPU/display stack. The standard EPG safety regression also passed. [11] [12]

## 14. Error Handling

The audited presentation paths provide redacted, user-facing messages. M3U registration retains a short failure message and recognizes the duplicate case. Theme-save failures continue to display “Unable to save theme” rather than persistence details. Existing error translation maps connection, timeout, authentication, client, and server failure families to domain-safe errors; this phase did not expose passwords, tokens, headers, or private URLs. [2] [13]

## 15. Onboarding

The first-run provider model remains **Add Provider → choose M3U/Xtream/MAG → enter protocol-appropriate information → load catalogue → watch**. The M3U branch is now materially simpler because URL and local-file choices are explicit, and internal provider identity is not requested up front. Xtream and MAG remain separate to avoid mixing unrelated requirements. [2] [8]

## 16. Accessibility

The implementation adds accessible names/tooltips for the M3U source, Browse action, Load action, theme selector, and Save Theme action. The PlayerShell native probe passed keyboard, navigation, sidebar, Space/fullscreen, and channel activation checks after the changes. [2] [3]

The audit did not conduct assistive-technology screen-reader validation or manual Windows Tab-order review; those are **NOT TESTED / P3** follow-ups rather than false claims of conformance.

## 17. Debug Diagnostics Assessment

No debug launcher was added. Existing diagnostics and tests already cover startup, packaged-VLC validation, DLL/runtime checks, provider-safe errors, player state, and recovery boundaries. A new launcher would be unjustified until a support scenario requires a narrowly scoped, redacted diagnostic bundle. Any future diagnostics must retain the established prohibition against printing passwords, tokens, cookies, authorization headers, or private stream URLs. [6] [7]

## 18. Comparative UX Findings

The conceptual comparison required by the specification was used only to identify fit-for-architecture patterns: direct primary-window navigation, explicit finite settings controls, source-first M3U setup, clear status, and no fake playback controls. It did not result in copying another application’s architecture or feature set. The changes are limited to patterns already compatible with the current Qt PlayerShell and provider boundaries.

## 19. Implemented Fixes

| Change | Components | Why it was safe and required |
|---|---|---|
| Direct Settings page | `player_shell.py`, `main_window.py` | Reuses the existing stacked-page navigation; preserves dialog fallback |
| Finite theme selector | `theme_settings_dialog.py`, PlayerShell settings page | Replaces unusual free text with the three valid `ThemePreference` values |
| M3U URL/file import simplification | `m3u_provider_dialog.py` | Keeps registration architecture intact; removes unnecessary user-facing ID work |
| Duplicate M3U message and load state | `m3u_provider_dialog.py` | Improves recoverability without exposing low-level details |
| Xtream service-subpath preservation | `smart_import.py`, `xtream_request_builder.py` | Fixes reproducible URL construction defect while removing credentials from normalized base URLs |
| Large-data acceptance harness | `phase27_large_data_probe.py` | Measures real Qt/model/parser boundaries deterministically; no provider access or secrets |

## 20. Regression Results

| Gate | Result | Evidence |
|---|---|---|
| Focused Phase 27 regressions | **PASS — 89 tests** | Smart Import, Xtream builder, M3U dialog, theme, MainWindow, native shell, performance, EPG, and VLC adapter suites |
| Final local non-presentation selection | **PASS — 99 collected cases** | Includes the Phase 27 probe; 72 pre-existing `aiohttp` deprecation warnings only |
| Native Qt PlayerShell probe | **PASS** | Offscreen subprocess passed direct settings plus pre-existing fullscreen/keyboard behavior |
| Large-data probe | **PASS** | 10,000-item datasets and zero remote cache-search calls |
| Ruff | **PASS** | `ruff check src/ tests/ providers/ scripts/` |
| Black | **PASS** | `black --check src/ tests/ providers/` |
| MyPy | **PASS** | 221 source files, no issues |
| Bandit | **PASS** | No high/medium findings; non-fatal parser comments / existing `nosec` warnings only |
| Dependency audit | **PASS** | No known vulnerabilities; local project itself is non-PyPI and therefore not auditable |
| Diff / credential indicator scan | **PASS** | `git diff --check`; no protected-file changes or matched sensitive indicators |
| Windows Portable EXE workflow | **PASS** | Native VLC lifecycle, PyInstaller EXE, packaged smoke, Qt smoke, sanitized PATH, artifact audit, checksum, metadata, artifact upload |

The first Windows run at `e9fc95b` failed only because POSIX-only `resource` was imported by the new probe. This was a confirmed cross-platform test defect, fixed in `6c7d15f`; the rerun passed all Windows gates. No test was weakened or reclassified as a warning. [10]

## 21. Remaining Issues

| ID | Severity | Classification | Exact reason and remaining action |
|---|---|---|---|
| R-01 | P1 | ENVIRONMENTAL BLOCKER | Authorized real-provider playback remains blocked by the previously observed provider/WAF response. Supply a fresh authorized provider locally to validate the full control-plane and continuity path. |
| R-02 | P2 | USABILITY ISSUE | Favorites, History, Providers, and EPG still retain legacy dialog-backed views. Migrate only after focused acceptance criteria and model/page reuse are designed. |
| R-03 | P2 | NOT TESTED | No real network/provider import timing, XMLTV fetch time, or real content artwork latency was measured. |
| R-04 | P3 | NOT TESTED | Manual Windows Alt+Tab, minimize/restore, multi-monitor fullscreen, assistive technology, and screen-reader review were outside this offscreen/local validation. |
| R-05 | P3 | NOT IMPLEMENTED BY DESIGN | No README screenshots were added because no new, verified desktop captures were produced; fabricated or stale captures were prohibited. |

## 22. Release Impact

The application version remains **0.1.5**. `pyproject.toml`, README badge block, CI workflow source, tags, release assets, and the existing `v0.1.5` release were not modified. The validated implementation commit was `6c7d15f46b41b2b22ba2745cc722fb00c1cd817b`, and `HEAD` matched `origin/main` at final evidence capture. The Windows build workflow ran from a non-tag push, so `publish-release` was skipped and no release was created. [10]

## 23. Final Classification

**FINAL CLASSIFICATION: B — IMPLEMENTATION AND PACKAGING ACCEPTED; REAL PROVIDER PLAYBACK ACCEPTANCE REMAINS BLOCKED.**

The user-feedback defects and high-value usability problems within the desktop application were implemented and regression-protected. The large-data presentation layer passed deterministic local acceptance, and the exact Windows portable build/smoke pipeline passed. However, no real authorized provider demonstrated end-to-end live/VOD playback continuity in this phase. Therefore, this is **not** a basis for another release; it is a validated branch improvement awaiting independent authorized-provider evidence.

## Required Final Audit Summary

| Required item | Outcome |
|---|---|
| Completed tasks | Targeted navigation, theme, M3U, Xtream subpath, large-data, tests, security, Windows packaging, and report tasks completed |
| Verification results | 89 focused tests, 99 final local non-presentation cases, static/security gates, and Windows run 32330586667 passed |
| Changes made | Six application files, nine regression/probe test files, and Phase 27 checklist/report artifacts |
| Blocked items | Real authorized provider end-to-end validation; manual multi-monitor/accessibility scenarios |
| Remaining actions | Obtain authorized provider evidence; design page migration for remaining dialog-backed library views; perform manual Windows UX/accessibility session |
| Final status | **Branch accepted; release not recommended; no release created** |

## References

[1]: `PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT.md` — prior authorized-provider validation status.  
[2]: `src/samotech_iptv/presentation/dialogs/m3u_provider_dialog.py` and `src/samotech_iptv/presentation/dialogs/theme_settings_dialog.py` — M3U and theme presentation contracts.  
[3]: `src/samotech_iptv/presentation/player_shell.py`, `src/samotech_iptv/presentation/views/main_window.py`, and `tests/player_shell_native_probe.py` — in-shell settings/navigation and native Qt evidence.  
[4]: `src/samotech_iptv/application/smart_import.py` and `src/samotech_iptv/infrastructure/providers/xtream_request_builder.py` — Xtream normalization and request construction.  
[5]: `tests/test_infra_vlc_player_adapter.py` — protected VLC adapter regression suite.  
[6]: `PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT.md` — provider blocker classification.  
[7]: `PHASE26_REAL_PLAYBACK_ACCEPTANCE_HARNESS.md` — real playback acceptance harness classification.  
[8]: `tests/test_application_smart_import.py`, `tests/test_infra_xtream_request_builder.py`, and `tests/test_presentation_provider_add_dialogs.py` — focused provider-flow regressions.  
[9]: `PHASE24_UI_UX_AUDIT.md` — previous fullscreen and keyboard acceptance baseline.  
[10]: [Windows Portable EXE workflow run 32330586667](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32330586667) — final Windows build and smoke evidence.  
[11]: `tests/phase27_large_data_probe.py` and `tests/test_phase27_large_data_probe.py` — deterministic large-data methodology and results.  
[12]: `src/samotech_iptv/presentation/dialogs/epg_grid_dialog.py` and `tests/test_presentation_epg_grid_dialog.py` — EPG rendering boundary and safety regression.  
[13]: `src/samotech_iptv/infrastructure/error_translation.py` — safe provider-error translation contract.
