# PHASE24_UI_UX_AUDIT

## 1. Executive Summary

Phase 24 audited the existing SamoTech IPTV Player PySide6 interface before real-provider validation. The work remained an interface-hardening phase, not a rewrite. The existing libVLC-only playback boundary, provider architecture, typed playback contracts, bounded recovery controller, credential boundaries, CI/CD, packaging, release metadata, tags, release assets, and README badge block were preserved.

The audit found three confirmed low-risk usability defects in the existing PlayerShell. Collapsed navigation labels were position-based rather than page-based, so optional EPG capability could mislabel later pages. Movie and Series catalogue load buttons were not disabled while the shared UI loading flag was active. The global keyboard event filter intercepted Space while the Fullscreen button had focus, preventing normal button activation. All three corrections were implemented through the existing presentation layer and covered by the native PlayerShell probe.

No provider protocol behavior, media backend, playback recovery behavior, network caching, release metadata, tag, or release asset was changed. The final classification is **UI AUDIT PASS WITH MINOR FINDINGS**. The remaining findings are environment-dependent Windows visual validation limits and intentionally unimplemented features, not confirmed regressions in the existing interface contracts.

> **Scope boundary:** Real IPTV provider compatibility was not tested in Phase 24 and is not claimed.

## 2. Existing Interface Inventory

| Interface area | Current implementation | Classification |
|---|---|---|
| Main window | `MainWindow` owns the Qt window, menu bar, status bar, native video surface, provider dialogs, and composed `PlayerShell`. | WORKING |
| Player surface | One `VlcVideoSurface` native `QFrame` attaches one native window handle to the injected player. | WORKING |
| Navigation | Home, capability-gated Live TV/Movies/Series, Favorites, History, Search, capability-gated EPG, Providers, and Settings. | WORKING after collapsed-label correction |
| Live channels | Provider selection, explicit channel loading, local search, category filtering, selection, Enter/double-click playback, and favorites. | WORKING |
| Movies | Explicit catalogue loading, local search/category/sort, card-style list, detail metadata, artwork, favorite, and play-selected flows. | WORKING within declared capabilities |
| Series/Episodes | Series → Season → Episode navigation, Back behavior, episode playback, adjacent episode controls, and local search. | WORKING within declared capabilities |
| EPG | Dialog-backed provider EPG and local XMLTV configuration/manual refresh paths. | WORKING where configured; provider data not tested |
| Favorites/History | Dialog-backed existing SQLite-backed library flows. | WORKING within existing contracts |
| Provider configuration | Combined Add IPTV Provider/Smart Import plus Xtream, M3U, MAG, provider list, edit, remove, and health paths. | WORKING within existing contracts |
| Settings | Main-window button, sidebar page, and Settings menu open the same existing theme settings dialog. | INTENTIONAL DUPLICATION |
| Menus | Providers, Library, Playback, and Settings menus with tested QAction wiring. | WORKING |
| Playback overlay | Context, state, progress, play/pause/stop, seek, volume, mute, tracks, subtitles, aspect, diagnostics, and fullscreen controls. | WORKING within player capabilities |
| Keyboard/mouse | Space, F, Escape, Left/Right/J/L, M, Enter, Up/Down, double-click, and mouse-move overlay reveal. | WORKING after fullscreen Space correction |

Evidence: `src/samotech_iptv/presentation/views/main_window.py`, `src/samotech_iptv/presentation/player_shell.py`, `src/samotech_iptv/presentation/widgets/vlc_video_surface.py`, `build/PHASE24_UI_INVENTORY.txt`, and `build/PHASE24_FOCUSED_UI_BASELINE.txt`.

## 3. Main Window Audit

The main window uses an existing `QMainWindow` with a top-level menu bar, status bar, native player surface, and `PlayerShell` central widget. The shell provides a top bar with sidebar toggle, product identity, provider selector, search field, provider badge, player status, and Settings button. The main layout uses nested Qt splitters for the player and catalogue areas rather than hard-coded separate windows.

The audit found no confirmed overlapping or duplicate player instances. `VlcVideoSurface` is created once by `MainWindow`, passed into `PlayerShell`, and attached to the injected player through the existing player-output path. The minimum native video size is explicit, and the shell uses splitter stretch factors to preserve the player and catalogue regions during resizing.

The current environment cannot prove Windows 11 100%, 125%, or 150% DPI geometry, physical multi-monitor layout, taskbar interaction, or Alt+Tab behavior. These are recorded as **NOT TESTED / REQUIRES WINDOWS VALIDATION**, not as implementation failures. No cosmetic layout redesign was introduced.

## 4. Player UI Audit

The player is an overlay-based interface over the one existing native libVLC surface. The overlay shows selected or playing context, typed public playback status, elapsed and duration labels, a seek slider for MOVIE/EPISODE content, playback buttons, relative seek buttons, restart, adjacent episode controls, volume, mute, native audio/subtitle menus, aspect-ratio selection, safe playback information, and fullscreen.

Control enablement is capability- and content-type-aware. LIVE playback does not expose VOD seek or restart actions. MOVIE and EPISODE playback expose position, duration, seek, restart, and episode adjacency only when the existing player port and content context support them. The UI renders typed states including Loading, Buffering, Reconnecting, Playing, Paused, Stopping, Stopped, Ended, and Playback error without exposing raw backend exceptions, resolved URLs, or provider credentials.

The player control audit found no missing P0 control. Previous/Next channel controls remain intentionally absent because no existing application contract defines channel adjacency; adding them would require a speculative playback change. Episode Previous/Next already exists where the existing series data supports it.

## 5. Fullscreen Audit

Fullscreen is implemented by toggling the existing top-level window between `showFullScreen()` and `showNormal()` in `PlayerShell._toggle_fullscreen`. The same `PlayerShell`, native video surface, and injected player remain in use. The code does not create a second player, reconstruct the media, or restart playback merely because the window state changes.

The fullscreen button updates its label between `Fullscreen` and `Exit fullscreen`, shows the player overlay, and restores keyboard focus to the button. The F shortcut enters or exits fullscreen, and Escape exits fullscreen when the window is fullscreen. The native PlayerShell probe passed F entry and Escape exit.

Physical Windows fullscreen geometry, multiple displays, taskbar behavior, and audio synchronization during a real Windows fullscreen transition require Windows desktop validation and were not available in the current environment. The hosted Windows workflow passed packaged-EXE and Qt/application smoke gates, but those gates are not a full visual multi-monitor review.

## 6. Playback Controls Audit

| Control | Existing behavior | Classification |
|---|---|---|
| Play/Resume | Calls the existing resume playback use case or content activation path. | WORKING |
| Pause | Calls the existing pause playback use case. | WORKING |
| Stop | Calls the existing stop playback use case and invalidates pending playback in MainWindow. | WORKING |
| Previous/Next channel | No existing capability or UI control. | INTENTIONALLY ABSENT |
| Previous/Next episode | Uses the existing selected episode list and guarded content playback path. | WORKING |
| Seek slider | Polls existing position/duration and calls existing seek fraction for VOD/episodes only. | WORKING |
| Current position/duration | Rendered from existing player-port position and duration. LIVE displays LIVE rather than a fabricated duration. | WORKING |
| Volume | Polls and sets existing player-port volume. | WORKING |
| Mute | Polls and toggles existing player-port mute. | WORKING |
| Fullscreen | Toggles the existing top-level window; F and Escape shortcuts are supported. | WORKING after keyboard correction |
| Audio/subtitles/aspect/info | Use existing player-port capabilities and safe status feedback. | WORKING within capability contract |
| Loading/buffering/recovery/error | Typed player state is mapped to user-safe status labels. | WORKING |

The UI does not duplicate playback logic. All controls delegate through existing application use cases or the existing `PlayerPort` surface.

## 7. Application Button Audit

| Button or action family | Evidence-based result |
|---|---|
| Login/connect/disconnect/logout | No separate implemented button contract was found. Provider selection and provider registration are the implemented entry points. No speculative controls were added. |
| Add Provider | WORKING through combined Add IPTV Provider and provider-specific dialogs. |
| Smart Import | WORKING through Add IPTV Provider → Smart Import; supports existing Xtream, M3U, and MAG detection paths. |
| Edit/Delete Provider | WORKING through ProviderListDialog and existing lifecycle use cases. |
| Refresh/Load/Search | WORKING for channels and declared content catalogues; loading disables duplicate load/search/favorite actions. |
| Favorites | WORKING through channel/content favorite controls and library dialog. |
| Categories/Channels | WORKING through capability-backed navigation, selectors, and dialogs. |
| Movies/Series/Episodes | WORKING within existing declared Xtream/content flows. |
| EPG | WORKING where the existing provider or local XMLTV path is configured. |
| Recent/History | WORKING through the existing History library dialog. |
| Settings | WORKING through top button, sidebar, and menu routes to the same dialog. |
| Import/Export | Smart Import exists; no general export contract exists, so no export button was invented. |
| About/Help/Update | No implemented application use case or safe path was found; these remain absent rather than dead. |
| Close/Back/Home | Window close is handled by Qt ownership; Series Back and Home navigation are implemented. |

The only confirmed button defect was the non-live load-button loading state, corrected by tracking content load buttons in the existing `_set_loading` path.

## 8. Menu Audit

`MainWindow` exposes four menus: Providers, Library, Playback, and Settings. Focused tests verify every action text and callback. Providers groups add-provider paths, channel/category browsing, EPG/XMLTV, and provider list. Library groups Favorites and History. Playback groups Pause, Resume, Stop, Start Recording, and Stop Recording. Settings contains the existing theme settings action.

The Settings menu, top Settings button, and sidebar Settings page are intentional discoverability routes to one dialog, not duplicated playback or provider logic. The combined Add IPTV Provider entry and direct Xtream/M3U/MAG actions are also intentional: the former supports discovery/import while the latter supports explicit configuration.

No obsolete or debug-only menu item was found. No menu simplification was required beyond documenting the existing grouping. Adding File/Help/About/Update structures without existing functionality would have been speculative.

## 9. UI State Audit

| State | Current presentation |
|---|---|
| LOADING | `● Loading`, `Loading…`, and disabled request buttons. |
| EMPTY | Explicit no-provider, no-channel, no-content, no-results, and empty-library text. |
| READY | `● Ready` and provider/content guidance. |
| PLAYING | `● Playing`, playing channel/content context, and active controls. |
| BUFFERING | `● Buffering` from typed player state. |
| STALLED | Not added as a public player state; existing recovery state is presented as `● Reconnecting`, consistent with the backend contract. |
| RECOVERING | `● Reconnecting` from typed `recovering` state. |
| ERROR | `● Playback error`, safe load/search/content error messages, and playback context. |
| OFFLINE/provider unavailable | `● Providers unavailable`, unavailable-content/category messages, and generic provider health status. |
| STOPPED/ENDED | Typed `● Stopped` and `● Ended` labels. |

Normal users are not shown raw exceptions, stack traces, resolved stream URLs, tokens, cookies, or credentials. The audit found no need to alter the existing status vocabulary or introduce a second recovery indicator.

## 10. Channel Experience Audit

Channel selection is distinct from playback. Clicking a channel selects it and updates the current-channel label; Enter or double-click invokes the existing guarded playback path. Up/Down keyboard navigation updates the selected row without starting playback. A selected channel can be added to Favorites without resolving or exposing its URL.

The existing category selector filters the loaded local catalogue without a new provider request. Search uses the existing application use case for live channels and local filtering for already loaded non-live content. Channel switching invalidates stale requests and pending playback through the existing generation/invalidation path.

Long names, duplicate names, missing logos, missing metadata, empty categories, and unavailable catalogue states use safe text rendering and do not change player ownership. No duplicate VLC/player instance is created by channel switching in the audited UI path.

## 11. Movies/Series Audit

Movies provide explicit loading, local filtering and sorting, selection, inline metadata, optional artwork, favorite, and play-selected behavior through the existing non-live application contracts. Seek, duration, relative seek, restart, and completion semantics are enabled only for the MOVIE content type when player capabilities are present.

Series provide explicit loading, catalogue selection, season discovery, episode discovery, Back navigation, episode activation, adjacent episode controls, and episode playback. The native probe passed Series → Season → Episode navigation and selected-episode playback.

LIVE-specific seek/restart/recovery behavior is not applied to normal MOVIE/EPISODE completion. The Phase 24 changes did not modify the media-type classification or playback recovery implementation.

## 12. EPG Audit

The interface includes a provider EPG dialog and a local XMLTV configuration/manual-refresh dialog. MainWindow routes both through existing use cases. The UI has explicit dialog-level loading, empty, and error handling based on the existing presentation tests and implementation.

Current EPG limitations are intentionally retained: no invented provider data, no automatic schedule, no new remote XMLTV source semantics, and no provider validation. Time formatting and current/next programme quality require populated authorized data and were not assessed against a real provider in this phase.

## 13. Keyboard/Mouse Audit

The existing practical shortcuts are:

| Input | Behavior |
|---|---|
| Space | Play/pause toggle unless the focused control is the Fullscreen button, where native button activation is preserved after UI-03. |
| F | Enter/exit fullscreen. |
| Escape | Exit fullscreen when active. |
| Left/Right, J/L | Relative VOD/episode seek through the existing player port. |
| M | Mute toggle. |
| Enter/Return | Activate selected channel/search/content item where the list owns focus. |
| Up/Down | Navigate channel/content list selection. |
| Mouse move | Reveal the player overlay. |
| Double-click | Activate channel/content list item. |

The native probe passed keyboard navigation, Enter playback, fullscreen F/Escape, Space play/pause, M mute, mouse overlay reveal, and stale playback protections. No conflicting shortcut was introduced.

## 14. Windows/DPI Audit

The hosted Windows workflow for the Phase 24 commit passed the unchanged Windows Portable EXE gates, including bundled VLC validation, native VLC lifecycle, Ruff, Black, MyPy, Windows non-Qt tests, one-file PyInstaller build, packaged-VLC smoke, Qt/application startup diagnostics, sanitized PATH/CWD validation, artifact audit, SHA256 generation, and artifact upload.

The workflow is not a physical visual review of Windows 11 at 100%, 125%, and 150% DPI. The following remain **NOT TESTED / REQUIRES WINDOWS VALIDATION**: clipped controls at each DPI, physical monitor arrangements, taskbar/Alt+Tab, minimize/restore visual state, dialogs behind the player, and real multi-monitor fullscreen geometry. No evidence justified a speculative layout rewrite.

## 15. Accessibility Audit

The interface has accessible names and tooltips for provider selection, search, navigation, channel lists, playback status, player controls, volume, mute, tracks, subtitles, aspect, diagnostics, fullscreen, content catalogues, and library/provider actions. Focus order is explicitly set across provider selector, search, navigation, channel list, load, search, and favorite controls.

The confirmed keyboard defect was limited to Space being intercepted while the Fullscreen button had focus. The event filter now lets that event reach the native button, while preserving global player shortcuts elsewhere. Destructive provider operations remain in their existing dialogs and lifecycle paths; no new destructive control was added.

Contrast, readable labels, visible disabled states, and predictable navigation are covered by the existing dark theme and offscreen contracts. A full Windows accessibility inspector review was not available.

## 16. Dead UI / Orphan Feature Audit

| Category | Finding |
|---|---|
| Visible button with no handler | None found among audited MainWindow/PlayerShell controls. |
| Code capability with no accessible UI path | Some capabilities such as general export, About, Help, Update, and channel adjacency have no implemented application contract; they are documented as absent, not silently dead. |
| Menu item with no implementation | None found in the existing four menus. |
| Duplicate controls | Settings and Add Provider have intentional multiple discoverability paths; no duplicate playback logic exists. |
| Debug/internal control exposed | No debug-only control was found in the audited UI. |
| Silent failure | Existing handlers use safe status/detail labels; the UI-only changes did not add a silent path. |
| Obscure-only feature | Smart Import is available from Add IPTV Provider and provider-specific actions remain directly discoverable. |

## 17. Implemented Changes

Three low-risk corrections were implemented in `src/samotech_iptv/presentation/player_shell.py`:

1. Collapsed navigation now maps compact labels by actual page identity rather than slicing a position-only list. Optional EPG absence no longer shifts labels for Search, Providers, or Settings.
2. Movie and Series load buttons are tracked and participate in the existing `_set_loading` enable/disable lifecycle, preventing duplicate visible actions during an active catalogue request.
3. Space events received by the focused Fullscreen button now fall through to native Qt button handling. The F/Escape fullscreen shortcuts and global Space play/pause behavior elsewhere remain unchanged.

`tests/player_shell_native_probe.py` adds deterministic assertions for all three corrections. No playback, provider, recovery, release, or security implementation was changed.

## 18. Intentionally Unchanged Areas

The following were explicitly preserved: libVLC through `python-vlc` as the sole media backend; `VlcVideoSurface` ownership; `PlaybackResource`/`ResolvedPlayback`; M3U, Xtream, and MAG provider semantics; the bounded liveness/recovery architecture; network caching and VLC media options; credential/keyring boundaries; CodeQL and CI definitions; PyInstaller packaging workflow; application version `0.1.5`; annotated tag `v0.1.5`; published v0.1.5 and v0.1.4 release assets; release metadata; and README badges.

The Enigma2 values `1`, `4097`, `5001`, `5002`, and `8193` were not introduced as VLC protocols or options. No provider validation or commercial compatibility claim was made.

## 19. Regression Test Results

| Verification | Result |
|---|---|
| Direct native PlayerShell probe | **PASS**; all existing and new probe markers passed. |
| Focused presentation tests | **PASS — 6 tests**: MainWindow, VLC surface, and PlayerShell wrapper. |
| VLC adapter suite | **PASS — 48 tests**. |
| Provider/application/security selection | **PASS — 66 tests**. |
| Official non-presentation corpus | **PASS — 885 tests** under the repository’s exact CI file-selection command. |
| Ruff | **PASS**. |
| Black | **PASS**; 372 files unchanged. |
| MyPy | **PASS**; 221 source files. |
| Bandit | **PASS** with existing informational nosec/comment warnings and no failed findings. |
| Security regression tests | **PASS — 14 tests**. |
| Secret scan | **PASS**; no authorized credentials found. |
| Prohibited Enigma2 diff scan | **PASS**; no prohibited values introduced. |
| `git diff --check` | **PASS**. |
| Hosted CI | **PASS** — run `32177305266`. |
| Hosted CodeQL | **PASS** — run `32177305185`. |
| Hosted Windows Portable EXE | **PASS** — run `32177305081`, including packaged artifact and path/CWD gates. |

The known Linux Qt collection segmentation fault for presentation modules remains an environment limitation when those modules are collected directly. The exact official non-presentation corpus passed, and the focused presentation probes passed.

## 20. Remaining Issues

The remaining issues are limited to untested environment-dependent behavior and intentionally absent features. A physical Windows 11 DPI/fullscreen/taskbar/multi-monitor review remains required for visual certification. Provider-populated EPG rendering and real-provider content states remain untested by design. General export, About, Help, Update, Logout, Disconnect, and Previous/Next channel capabilities have no existing contracts and were not invented.

No confirmed P0 UI defect remains. The three confirmed P1 defects identified by the audit were corrected and re-verified.

## 21. Provider-Test Dependencies

Phase 24 did not perform provider validation. The UI can be validated with synthetic and provider-neutral DTOs, but populated Xtream/M3U/MAG runtime acceptance requires authorized provider data and is governed by the prior provider/release evidence. The existing real-provider classification remains **NOT TESTED / BLOCKED / REQUIRES AUTHORIZED PROVIDER VALIDATION** where applicable.

Provider-dependent checks still requiring authorized evidence include populated channel/logo/metadata quality, real EPG current/next display, provider-specific Movie/Series catalogues, sustained media playback, and commercial compatibility. No Phase 24 interface result changes those classifications.

## 22. Final Classification

# UI AUDIT PASS WITH MINOR FINDINGS

The existing interface is complete enough for the declared current application capabilities and the confirmed P0/P1 interface defects have been corrected without changing playback, provider, security, recovery, CI/CD, packaging, or release architecture. The remaining minor findings are the documented Windows visual/DPI validation boundary and intentionally unimplemented features that have no existing application contract.

This classification is not a real IPTV provider compatibility certification and does not claim a populated provider playback pass.

## Evidence References

1. `build/PHASE24_UI_INVENTORY.txt` — interface inventory.
2. `build/PHASE24_UI_AUDIT_FINDINGS.md` — pre-change forensic findings ledger.
3. `build/PHASE24_FOCUSED_UI_BASELINE.txt` — pre-change presentation baseline.
4. `build/PHASE24_UI_FIX_PROBE_RERUN.txt` — direct post-change PlayerShell probe.
5. `build/PHASE24_FOCUSED_UI_TESTS.txt` — focused presentation regression result.
6. `build/PHASE24_PLAYBACK_PROVIDER_REGRESSIONS.txt` — playback/provider/security regression result.
7. `build/PHASE24_OFFICIAL_NONPRESENTATION.txt` — exact official non-presentation corpus result.
8. `build/PHASE24_QUALITY_SECURITY_GATES.txt` — local quality and security gates.
9. Hosted CI run `32177305266` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305266
10. Hosted CodeQL run `32177305185` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305185
11. Hosted Windows Portable EXE run `32177305081` — https://github.com/SamoTech/samotech-iptv-player/actions/runs/32177305081
