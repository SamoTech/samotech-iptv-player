# Phase 28 UI, Visual Design & Menu Review

## Complete Audit Summary

| Surface | Evidence-based finding | Severity | Decision |
|---|---|---:|---|
| Visual hierarchy | PlayerShell has a coherent dark player-first hierarchy, shared spacing/radius tokens, explicit empty panels, capability-gated navigation, clear status labels, and local loading states. | None | Preserve. |
| Typography and spacing | The shell uses established headings, eyebrow/kicker labels, page titles, muted explanatory copy, and a consistent spacing scale. | None | Preserve. |
| Navigation | Home, Live TV, Movies, Series, Favorites, History, Search, EPG, Providers, and Settings are capability-gated and keyboard reachable. Compact sidebar uses text/symbol fallbacks rather than image assets. | None | Preserve. |
| Provider setup discovery | `MainWindow` creates **Add IPTV Provider…** but omits it from the Providers menu. The only general Smart Import/Manual Add entry point is therefore not reachable from the normal menu. | **P1** | Expose the existing action first in Providers. |
| Opaque visible provider selection | PlayerShell's active provider selector remains editable and advertises “Select provider or enter ID”, despite safe registered-provider labels already being available. | **P1** | Make it a non-editable safe selector and remove manual opaque-ID entry from normal UI. |
| Settings discoverability | A one-item `Settings` menu requires an unnecessary second activation before opening the direct in-shell Settings page. | P2 | Expose Settings as a direct menu-bar action. |
| Diagnostics discoverability | Safe diagnostics are supported through Info in player overlay, but are absent from top-level navigation/menus. | P2 | Expose the existing safe dialog through Playback. |
| Fullscreen discoverability | Fullscreen has an explicit overlay button, tool tip, Escape/F shortcuts, and safe native window handling. | None | Preserve; do not duplicate in a menu this cycle. |
| Player controls | Live mode correctly disables VOD seeking/restart; VOD/episodes expose seek, resume, next/previous episode, volume, tracks, subtitles, aspect ratio, retry, diagnostics, and fullscreen. | None | Preserve. |
| Menus | Providers, Library, Playback, and Settings expose valid existing functionality; menu grouping is mostly clear but misses the combined provider entry and safe diagnostics. | P1/P2 | Add only existing actions; no fake Tools/Help menu. |
| Icons | The UI uses text labels and a small compact sidebar glyph set; no established icon system or image asset pipeline exists. | None | Do not add random icon dependencies. |
| Dialog/window management | Provider dialogs are transient-owned and direct in-shell settings is preferred; no evidence justifies a windowing rewrite. | None | Preserve. |
| Themes | Application startup applies persisted System/Light/Dark preferences through the existing theme engine. PlayerShell also has a dark-oriented local stylesheet, so exact visual behavior should be manually verified before a token rewrite. | P3 validation gap | Defer rather than alter unmeasured visual style. |
| Accessibility | Meaningful accessible names/tooltips exist for navigation, provider selection, controls, search, content lists, settings, and fullscreen. Menu accessibility follows native Qt actions. | None | Preserve and extend names for new actions. |
| Empty/error/loading states | Explicit provider, channel, category, search, content, artwork, playback retry, EPG, and theme feedback states already exist and do not leak secret details. | None | Preserve. |
| Large playlists/EPG | Existing 10k deterministic evidence, explicit load, local search/filter/sort, models/delegates, and stale-request tokens support current scope. | None | Preserve; no unexplained 50k/100k work. |
| Reddit feedback | Historical menu/setup/settings/opaque-ID feedback maps directly to the two discoverability fixes. Real provider/auth reports remain blocked until safe reproduction evidence arrives. | P1 external / P1 UI | Implement only local UI exposure fixes. |

## Capability Exposure Matrix

| Existing capability | Current entry point | Gap | Approved exposure |
|---|---|---|---|
| Smart Import / Manual Add | Constructed `add_provider_action`; otherwise individual protocol actions | Combined guided entry is not in Providers menu | Add existing `Add IPTV Provider…` action first in Providers menu |
| Provider selection | Safe provider labels plus editable ID fallback | Normal UI encourages opaque ID entry | Keep safe labels/data, disable manual editing |
| Safe diagnostics | Player overlay Info button | Hidden when overlay is dismissed; not in menu | Add existing action to Playback menu |
| Settings | Direct in-shell page plus a one-item menu | Redundant two-step menu | Direct menu-bar Settings action |
| Fullscreen | Overlay button and F/Escape shortcuts | No verified gap | Preserve |
| Audio/subtitles/aspect | Overlay controls | No verified gap | Preserve |
| Favorites/history/EPG | Capability-specific pages/dialogs | No verified gap | Preserve |

## Cross-Role Review

The Interface & Visual Design Engineer, UI/UX Principal, Provider Protocol Engineer, Playback Engineer, Security Engineer, Performance Engineer, QA Engineer, Windows Specialist, Release/CI Engineer, and Chief Architect agree that the selected work is presentation-only. It does not change provider setup semantics, account/capability truth, provider/media boundaries, PlayerPort/libVLC lifecycle, settings persistence, diagnostic data, secret handling, performance workloads, packaged runtime, or release logic.

The Independent Design Auditor challenged whether adding menu entries would create duplicate navigation. The challenge was accepted in part: no new generic Tools or Help menu, no duplicate Fullscreen control, and no icon-library expansion will be added. It was rejected for provider setup and diagnostics because their existing functionality lacks a normal top-level discoverability path. The direct Settings action replaces—not duplicates—the one-item Settings menu.

> **Approved implementation:** expose the existing combined provider-entry action, convert the active provider picker to a safe non-editable selector, expose existing safe diagnostics through Playback, and replace the redundant one-item Settings menu with its direct existing action. No other presentation rewrite is approved.

## References

[1]: [`PHASE28_UI_INVENTORY.json`](PHASE28_UI_INVENTORY.json)
[2]: [`src/samotech_iptv/presentation/views/main_window.py`](../../src/samotech_iptv/presentation/views/main_window.py)
[3]: [`src/samotech_iptv/presentation/player_shell.py`](../../src/samotech_iptv/presentation/player_shell.py)
[4]: [`tests/test_presentation_main_window.py`](../../tests/test_presentation_main_window.py)
