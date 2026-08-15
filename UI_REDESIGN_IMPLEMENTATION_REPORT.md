# SamoTech IPTV Player — UI Redesign Implementation Report

**Status:** implementation and validation complete; **no commit or push was created**.

## Executive summary

This report consolidates the pre-edit audit, incremental implementation, regression coverage, scalability measurements, quality checks, and final scope review for the six player-first interaction improvements in the existing PySide6 application. The work remained inside the established presentation architecture. It did not rewrite the application, add a web implementation, introduce another UI framework, or alter provider, protocol, credential, VLC, persistence, or deployment behavior.

The revised `PlayerShell` now makes selected, loading, playing, and error channel identity explicit. It maintains a persistent category control, filters an already loaded catalogue locally, keeps a selection distinct from an intentional playback request, and preserves the existing cache-first application search boundary. Delayed actions in both the primary shell and the legacy channel browser now capture immutable `ChannelDTO` values before asynchronous work begins, preventing an intervening catalogue replacement from retargeting a user action.

| Validation area | Final result |
|---|---|
| Full pytest suite | **680 passed, 0 failed** |
| Native offscreen Qt probe | **PASS** |
| 39,753-channel performance probe | **PASS**; no resolver, provider-search, or catalogue-reload calls |
| Black | **PASS** (`290 files would be left unchanged`) |
| Ruff | **PASS** |
| `git diff --check` | **PASS** |
| Mypy | **11 pre-existing errors in 4 files; no task-introduced errors** |
| Commit / push | **Not performed** |

## Pre-edit architecture audit

### Scope and Git baseline

The audit was completed against the current `main` branch before production source edits. `HEAD` and `origin/main` both resolved to `98326ceec5ddb83d7679f6ff93696fa7e8d53e43`; the working tree was clean. The existing history includes the player-first shell redesign commit `98326ce feat(ui): redesign IPTV player experience` and prior desktop composition integration fixes.

| Git check | Result |
|---|---|
| Branch | `main` |
| Local HEAD | `98326ceec5ddb83d7679f6ff93696fa7e8d53e43` |
| `origin/main` | `98326ceec5ddb83d7679f6ff93696fa7e8d53e43` |
| Working tree before edits | Clean |
| Remote | `https://github.com/SamoTech/samotech-iptv-player.git` |

### Current UI structure

`MainWindow` owns the `VlcVideoSurface`, native menu actions, dialogs, and application-use-case references. In a full PySide6 environment it composes `PlayerShell` as the central widget; reduced legacy fake-Qt tests fall back to the raw video surface. `PlayerShell` supplies a dark player-oriented shell with a provider selector, search field, model-backed navigation rail, `QStackedWidget` pages, a `QListView` bound to `ChannelListModel`, playback controls, and existing Favorites/History/EPG/Provider/Settings dialog entry points.

The current geometry is a horizontal splitter of navigation, pages, and player. This is player-aware but does not fully establish the requested vertical hierarchy of player, context, category navigation, then catalogue. Categories still use a modal `CategoryBrowserDialog` backed by a `QListWidget`, and the legacy channel browser remains available as a modal compatibility path.

### Current channel identity and selection flow

`ChannelDTO` is immutable and contains stable `id`, `provider_id`, `stream_id`, optional `category_id`, optional `number`, and safe display fields. `ChannelListModel` stores canonical DTO references in a private list, exposes `channel_at(row)`, and replaces all rows through one `beginResetModel()` / `endResetModel()` batch. It does not allocate one item widget per channel.

Within `PlayerShell`, mouse or keyboard selection changes the `QListView` current index only. Enter and double-click obtain the DTO synchronously with `channel_model.channel_at(row)` and pass the DTO reference into asynchronous playback; favorites likewise capture a DTO before scheduling. This is already safer than delayed index re-resolution. However, the shell has no explicit `selected_channel`, `playing_channel`, `loading_channel`, or `playback_error_channel` state. Its `current_channel_label` updates only after successful playback, so selection, loading, failure, catalogue replacement, filtered search, and category changes do not all have a consistent visible identity context.

The legacy `ChannelBrowserDialog` still schedules favorites and playback by row and resolves `self._channels[row]` inside asynchronous methods. A catalogue replacement between scheduling and execution could therefore retarget or fail. It requires targeted hardening while retaining its existing modal compatibility contract.

### Current playback flow

`MainWindow.play_registered_channel()` attaches the existing native video output and delegates to `PlayRegisteredChannel`. The use case resolves only the registered provider’s playback capability, delegates to `PlayChannel`, and records history after success. `PlayerPort` supports play, pause, resume, stop, recording, native output attachment, `is_playing`, and `is_recording`; it does not expose volume, mute, current stream, or detailed error state.

Selection does not need to change the playback/provider boundary. Presentation code can make selection state visible and capture DTOs before playback without touching stream resolution, MAG protocol, M3U/Xtream providers, credentials, or VLC internals.

### Current browse, cache, and search flow

`BrowseChannels` resolves a catalogue provider and loads channels. Successful whole-catalogue requests write a provider-scoped `ChannelCatalogueCache` snapshot; category-specific browse does not replace that complete snapshot. `SearchRegisteredChannels` searches the existing cache first and only resolves the provider/search capability when no cached snapshot exists. Empty cache-backed search returns the first cached rows up to the requested limit. Provider update and removal use cases invalidate the shared cache on successful operations.

`PlayerShell` invokes this existing search use case. It does not create another cache, does not reload the catalogue for a search, and uses request generations to prevent stale load/search response overwrites. The presentation layer must preserve this contract and should only extend local category filtering against currently loaded DTOs or call the existing category-aware browse path deliberately.

### Existing reusable components and regression points

| Component | Reuse or preservation decision | Regression risk |
|---|---|---|
| `VlcVideoSurface` | Preserve unchanged as the native player-output host | Any surface ownership change risks VLC output attachment |
| `ChannelListModel` | Preserve model/view and batched reset architecture | Must retain 39,753-record efficiency and identity access |
| `ChannelCatalogueCache` / `SearchRegisteredChannels` | Preserve unchanged as the one shared cache and cache-first search boundary | UI must not create a competing cache or trigger provider search unnecessarily |
| `PlayRegisteredChannel` | Preserve unchanged | UI must not move stream/provider resolution into presentation |
| `FavoritesLibraryDialog` / `HistoryLibraryDialog` | Preserve existing entry points and persistence behavior | Do not alter repository/persistence semantics |
| `CategoryBrowserDialog` | Preserve as a legacy modal entry point; do not use it as primary player workflow | Do not reintroduce per-channel widgets in the main catalogue |
| `ChannelBrowserDialog` | Preserve as compatibility UI but harden delayed DTO targeting | Existing row-index callback flow can become stale |
| `MainWindow` menus and actions | Preserve menu/dialog access and reduced-fake-Qt fallback | Constructor and fake harness compatibility |

### Exact intended changes

The incremental implementation was constrained to presentation behavior and presentation tests. The expected source changes were `presentation/player_shell.py`, `presentation/dialogs/channel_browser_dialog.py`, and `presentation/views/main_window.py` only to pass the already-composed `LoadCategories` use case into the shell. Presentation and dedicated performance/native-probe tests cover explicit state, selection-versus-playback, category filtering, cache-first search behavior through mocks, and A/B/C identity safety.

### Files intentionally out of scope

The following files and areas were intentionally untouched: MAG authentication, MAC handling, MAG handshake/protocol/transport, M3U protocol, Xtream protocol, provider session/runtime implementation, provider credentials, stream resolution, `VlcPlayerAdapter`, player composition, domain entities, persistence repository behavior, deployment configuration, and CI configuration.

### Risks and planned mitigations

The primary risks were stale index targeting in the legacy dialog, accidental regressions in reduced fake-Qt tests, model/view scalability regression, and a UI-only category feature accidentally triggering unnecessary provider fetches. The implementation captures immutable `ChannelDTO` targets before delayed actions; preserves model resets instead of introducing row widgets; uses existing application use cases; applies category selection locally over loaded DTOs where possible; and validates provider, cache, resolver, playback, favorites, and history call counts through focused probes.

## Implementation and architecture impact

The implementation is deliberately presentation-layer only. `MainWindow` receives no new playback, search, or provider responsibility: it passes its already-composed `LoadCategories` use case into `PlayerShell` as an optional keyword argument. The optional constructor argument preserves compatibility with reduced fake-Qt harnesses and older construction sites.

| Changed file | Change and architectural effect |
|---|---|
| `src/samotech_iptv/presentation/player_shell.py` | Implements the player-first interaction state, persistent category selector, local catalogue rendering, identity-safe playback state transitions, and keyboard context updates while retaining the existing model/view and use-case boundaries. |
| `src/samotech_iptv/presentation/views/main_window.py` | Wires the existing category-loading use case into the shell; it does not modify native video attachment, menus, provider composition, or playback resolution. |
| `src/samotech_iptv/presentation/dialogs/channel_browser_dialog.py` | Captures a `ChannelDTO` before delayed favorite or playback work and accepts either a DTO or legacy row value for backward compatibility. |
| `tests/player_shell_native_probe.py` | Extends the real offscreen Qt regression probe for the new interaction states, local categories, and legacy-dialog stale identity handling. |
| `tests/player_shell_performance_probe.py` | Adds the isolated exact-39,753-channel offscreen performance and call-boundary probe. |
| `tests/test_presentation_01_player_shell_performance.py` | Runs the large-catalogue probe from pytest and asserts data volume, identity, and zero external-call invariants. |
| `UI_REDESIGN_IMPLEMENTATION_REPORT.md` | Provides this single consolidated audit, implementation, validation, and handoff record. |

### 1. Explicit selected, loading, playing, and error context

`PlayerShell` now owns explicit `selected_channel`, `playing_channel`, `loading_channel`, and `playback_error_channel` state. `_update_channel_context()` renders distinct selected and playback identity instead of conflating a highlighted row with the stream currently active in the player. This gives a user a stable answer to both questions: **what is selected** and **what is playing**.

During a playback request, the shell records the captured DTO as loading. On success, it promotes that same DTO to playing and clears transient loading/error state. On failure, it records the error identity without falsely claiming that the selected channel is playing. The state transition is guarded against stale completions so an earlier asynchronous request cannot overwrite context for a later request.

### 2. Selection is intentionally separate from playback

The new `_select_index()` path updates selection and contextual labels only; it does not start stream playback. Mouse selection, keyboard navigation, and view-current-index changes therefore remain cheap presentation interactions. Explicit user actions such as Enter and double-click continue to initiate playback by first obtaining the immutable DTO synchronously and then scheduling the existing playback use case.

This preserves the established provider and player architecture while preventing accidental stream changes during catalogue exploration. The native probe verifies selection-without-playback directly.

### 3. Persistent category navigation with local filtering

The shell includes a persistent `QComboBox` category selector. `MainWindow` supplies the existing category loader, while the shell keeps category selection local to the loaded catalogue and makes it available alongside search rather than behind a primary modal workflow. `_render_active_catalogue()` combines the current category and query constraints against in-memory `ChannelDTO` values, then replaces the `ChannelListModel` in one batch.

The category selector preserves the selected category through normal list interactions and provides an all-categories state. The implementation does not introduce per-channel widgets, a second cache, or a provider-level filtering path for this local interaction. The native probe checks that category filtering returns the expected catalogue subset.

### 4. Cache-first search and zero-query preservation

The existing `SearchRegisteredChannels` use case remains the single search boundary. The shell now short-circuits an empty query to the already loaded catalogue and applies local rendering, rather than issuing an avoidable search operation. For non-empty search text, it uses the existing cache-first use case and preserves request-generation protection against stale search responses.

This keeps provider search, resolver, and catalogue reload work off the keystroke path when a cache is available. It also ensures that clearing a query promptly restores the loaded catalogue and current category context. The large-catalogue probe confirms zero resolver calls, zero provider-search calls, and zero catalogue-reload calls for all cache-first search scenarios.

### 5. Immutable DTO capture for delayed actions and stale-response safety

The primary shell now transitions playback using the captured `ChannelDTO` identity instead of a later-resolved row. Its request-generation checks prevent stale load/search/playback results from replacing newer visible state. The legacy `ChannelBrowserDialog` is hardened with the same principle: `_schedule_add_favorite()` and `_schedule_selected_channel()` capture the DTO before scheduling, while `add_favorite()` and `_play_channel()` accept `ChannelDTO | int` so existing row-based callers remain compatible.

The native A/B/C regression case replaces the underlying catalogue between scheduling and execution and verifies that the original chosen channel remains the target. This closes the legacy retargeting risk without replacing the compatibility dialog or altering favorites/history persistence semantics.

### 6. Keyboard continuity and scalable model-backed catalogue behavior

Up/Down navigation now synchronizes the explicit selected-channel context, so keyboard users receive the same visual identity feedback as mouse users without starting playback. Enter retains its explicit activation role. The catalogue remains a `QListView` backed by `ChannelListModel`, which exposes DTO identity through indexed access and performs batch reset replacement rather than creating one widget per row.

This preserves fast navigation at large catalogue sizes and keeps focus, row selection, search, category filtering, and playback activation distinct. The native probe verifies keyboard accessibility, and the performance probe verifies correct first/middle/last channel identity across exactly 39,753 records.

## Native Qt validation

The focused probe executed with `QT_QPA_PLATFORM=offscreen` against real PySide6 widgets. It completed successfully with `player_shell_native_probe=PASS`. The harmless platform-plugin message `This plugin does not support propagateSizeHints()` was emitted in offscreen mode and did not affect assertions.

| Native probe assertion | Result |
|---|---|
| Records loaded | `records=3` |
| Stale playback identity protection | `PASS` |
| Legacy dialog stale-identity protection | `PASS` |
| Async error-state cleanup | `PASS` |
| Stale request protection | `PASS` |
| Provider selection | `PASS` |
| Selection without playback | `PASS` |
| Local category filtering | `PASS` |
| Keyboard accessibility | `PASS` |

## 39,753-channel performance and call-boundary validation

The dedicated offscreen probe creates exactly **39,753** synthetic immutable channel DTOs and exercises model replacement, first/middle/last identity access, selection, empty reset, result replacement, and the cache-first search path. The recorded benchmark values below are the captured final validation measurements. They are provided as order-of-magnitude local measurements, not a user-device performance guarantee.

| Operation | Measurement | Assertion / observed result |
|---|---:|---|
| Initial model replacement | **0.091 ms** | 39,753 model rows |
| Selection latency | **0.026 ms** | Middle DTO identity preserved (`channel-19877`) |
| Empty replacement | **0.032 ms** | 0 model rows |
| Search-result replacement | **1.340 ms** | 3,975 model rows |
| Cache-first empty search | **0.031 ms** | 39,753 results |
| Cache-first common search: `arena` | **1.230 ms** | 3,975 results |
| Cache-first rare search | **1.018 ms** | 1 result |
| Cache-first no-match search | **1.047 ms** | 0 results |
| Cache-first repeated search | **1.184 ms** | 3,975 results |
| Clear search | **0.006 ms** | 39,753 results restored |

| External boundary | Expected | Observed |
|---|---:|---:|
| Resolver calls | 0 | **0** |
| Provider-search calls | 0 | **0** |
| Catalogue-reload calls | 0 | **0** |

The probe also verified that the first, middle, and last IDs remained `channel-00001`, `channel-19877`, and `channel-39753`. This confirms that fast model replacement did not sacrifice canonical DTO identity.

## Full test and quality results

The complete suite was executed after the new probe wrapper was added and formatted. Test collection reported **680 tests collected in 0.25 seconds**, and the full run completed with all 680 passing. Four pre-existing `aiohttp` deprecation warnings about bare handlers were reported by `tests/test_http_session_lifecycle.py`; they were warnings only and did not represent test failures.

| Command / gate | Result | Interpretation |
|---|---|---|
| `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` | **680 passed, 0 failed** | Full regression suite passes, including the new pytest-wrapped performance probe. |
| `QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python tests/player_shell_native_probe.py` | **PASS** | Real Qt widget interactions and compatibility paths pass. |
| `QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python tests/player_shell_performance_probe.py` | **PASS** | Exact 39,753-record and cache-boundary assertions pass. |
| `.venv/bin/black --check src tests` | **PASS** | 290 files would be left unchanged. |
| `.venv/bin/ruff check src tests` | **PASS** | No lint diagnostics. |
| `git diff --check` | **PASS** | No whitespace errors. |
| `.venv/bin/mypy src` | **11 errors, inherited** | Static baseline is not clean; task introduces none. |

### Mypy classification

The 11 mypy diagnostics are pre-existing and confined to four files. They are unrelated to this task’s asynchronous identity or player-shell behavior. No type-checker diagnostic was added in a new task file, and no new production file was introduced.

| File | Count | Existing diagnostic class |
|---|---:|---|
| `presentation/viewmodels/channel_list_model.py` | 4 | Two unused `type: ignore` comments and two PySide6 override-signature incompatibilities |
| `presentation/dialogs/history_library_dialog.py` | 2 | Unused `type: ignore` comments |
| `presentation/dialogs/favorites_library_dialog.py` | 2 | Unused `type: ignore` comments |
| `presentation/views/main_window.py` | 3 | Unused `type: ignore` comments |
| **Total** | **11** | **Pre-existing baseline diagnostics; no regression introduced by this work** |

## Regression and security/scope analysis

The changes retain the existing application use cases for provider selection, channel browsing, searching, category loading, playback, favorites, and history. `PlayerShell` remains a view/controller boundary: it stores presentation state and invokes supplied behavior, but does not resolve streams, access credentials, construct provider clients, or control VLC internals. `ChannelListModel` remains the data structure responsible for catalogue rows; no per-row widget allocation, custom cache, or network fallback was introduced.

The final path review found changes only in the three intended presentation source files, one extended native probe, two new performance-test files, and this report. In particular, no final diff path matched MAG, MAC, provider transport, VLC, M3U, Xtream, credential, secret, deployment, Docker/Compose, or CI/GitHub configuration areas. No secret, credential, endpoint, or personally identifying value was added. The implementation therefore remains within the agreed presentation-only security and scope boundary.

| Protected area | Final review result |
|---|---|
| MAG authentication, MAC handling, protocol, and transport | Untouched |
| M3U and Xtream provider protocols | Untouched |
| Provider credentials, session/runtime behavior, and stream resolution | Untouched |
| VLC adapter, native player internals, and video-output attachment | Untouched |
| Domain model and persistence/Favorites/History repository semantics | Untouched |
| Deployment, containers, CI, and GitHub configuration | Untouched |

## Remaining limitations

The changes intentionally do not add player telemetry, volume/mute/current-stream APIs, network-status reporting, or new persistence. Category filtering is a local interaction over the loaded catalogue; it does not attempt to redefine provider-side category retrieval. The modal `CategoryBrowserDialog` and `ChannelBrowserDialog` remain available for compatibility, with the latter hardened only at the delayed-action identity boundary.

Performance values were measured in the local offscreen Qt environment and should be treated as comparative validation evidence rather than a service-level guarantee for every end-user machine, display driver, provider catalogue, or network condition. Mypy remains non-clean because of the inherited PySide6 typing and unused-ignore diagnostics listed above; resolving that baseline is useful maintenance work but was outside this constrained interaction task.

## Final Git status and handoff

The final review confirmed that `HEAD` remains `98326ceec5ddb83d7679f6ff93696fa7e8d53e43`. There was **no commit, push, reset, revert, clean, or deployment action**. The working tree intentionally contains the implementation and its report for review.

| Working-tree category | Files |
|---|---|
| Modified tracked source | `player_shell.py`, `main_window.py`, `channel_browser_dialog.py` |
| Modified tracked test | `tests/player_shell_native_probe.py` |
| New untracked test files | `tests/player_shell_performance_probe.py`, `tests/test_presentation_01_player_shell_performance.py` |
| New untracked documentation | `UI_REDESIGN_IMPLEMENTATION_REPORT.md` |
| Initial Git baseline still checked out | `98326ceec5ddb83d7679f6ff93696fa7e8d53e43` |

## Recommended next step

Please review the uncommitted implementation and this consolidated report, then exercise the desktop application manually with a representative provider catalogue: select with mouse and keyboard, confirm that selection does not start playback, activate a channel explicitly, switch categories, search and clear search, and use the legacy browser’s favorite/play paths. If the observed behavior is accepted, provide explicit approval before any commit or push is considered. A separate maintenance task can address the 11 inherited mypy diagnostics without mixing static-baseline cleanup into this validated UI interaction change.

---

# Content-Type-Aware Player-First Evolution Addendum

**Status:** complete and uncommitted. This addendum records the bounded architecture/UX audit and implementation pass requested after the Phase 6 player-first work. It is part of the same consolidated report; no prior Phase 6 change was discarded, reset, reverted, cleaned, stashed, or overwritten.

## Objective and preserved baseline

The application was evolved from a live-channel-centric shell into a **provider-capability-driven, content-type-aware presentation layer**. The stress-test figure of **39,753** remains a synthetic live-catalogue cardinality only; it is not treated as a product assumption, provider limit, or UI identity. Catalogue size remains dynamic and provider-specific.

The preserved starting point was the uncommitted Phase 6 working tree on `HEAD` `98326ceec5ddb83d7679f6ff93696fa7e8d53e43`. Its player-first shell, `QListView`/`QAbstractListModel` design, `ChannelListModel`, selection-versus-playback separation, explicit live state, immutable DTO capture, stale-response protection, local live category filtering, cache-first live search, and 39,753-channel validation all remained present and passing.

| Guardrail | Final result |
|---|---|
| Phase 6 player-first source and test changes | Preserved and extended; not replaced |
| `ChannelListModel` live path | Preserved unchanged |
| Live `QListView`/batched-model performance path | Preserved unchanged |
| Live selection versus playback semantics | Preserved and revalidated |
| `ChannelCatalogueCache` and `SearchRegisteredChannels` boundary | Preserved unchanged |
| Commit, push, reset, revert, clean, stash, or deployment | Not performed |

## Architecture audit findings

The domain layer already contains immutable canonical entities for `Channel`, `Movie`, `Series`, `Episode`, and shared `Category`. `Movie` carries stable identity, provider identity, stream identity, category, poster/plot/rating/year metadata. `Series` carries stable provider and catalogue identity with category and metadata, but not an episode collection. `Episode` carries series identity, season, episode number, and stream identity. The existing application DTO layer was live-only: it exported `ChannelDTO` and category DTOs but no Movie, Series, Episode, or cross-content presentation transfer objects.

The provider capability layer already distinguishes `LIVE`, `VOD`, `SERIES`, `CATEGORIES`, `EPG`, `CATCHUP`, `SEARCH`, and stream resolution. Its interfaces already expose separate live/VOD/series category calls, `load_movies()`, and `load_series()`. The concrete Xtream adapter already advertises and implements live, VOD, series, category, EPG, and live stream-resolution behavior. MAG and M3U remain live-focused according to their declared runtime capability sets. No adapter, protocol, session, credential, or transport implementation was changed.

| Content family | Existing canonical entity | Existing provider capability | Existing application path before this work | Result of this work |
|---|---|---|---|---|
| Live TV | `Channel` / `ChannelDTO` | `CatalogProvider`, `SearchProvider`, `PlaybackProvider` | Browse, cache-first search, categories, EPG, playback | Preserved exactly |
| Movies / VOD | `Movie` | `VodProvider.load_movies()` | No application DTO or browse use case | Added safe projection and explicit browse path |
| Series | `Series` | `SeriesProvider.load_series()` | No application DTO or browse use case | Added safe projection and explicit browse path |
| Episodes | `Episode` | No episode loader or episode playback resolver | No path | Declared in presentation type vocabulary; explicitly reported unavailable |
| Categories / genres | `Category` / `CategoryDTO` | Per-family category methods | Live-only category use case | Existing use case extended with a compatible content-family selector |

The audit also found that `ProviderMetadata.capabilities` is presentation-safe but is populated with all-false defaults by the registry listing adapter. Therefore, guessing from provider type would not satisfy a capability-driven UI. The implementation instead resolves the registered runtime provider through the existing factory/runtime-cache path and reads its `CapabilityProvider.supported_capabilities()` declaration once on provider selection. This does not query catalogue data, credentials, streams, or provider transport.

## Architecture decision and rationale

The chosen strategy is **B: retain `ChannelListModel` for Live TV and complement it with an equivalent lightweight `ContentListModel` for Movie/Series projections**. This preserves the live model’s established contract and its Phase 6 cache/search behavior rather than overloading `ChannelDTO` with non-live fields. The complementary model has the same essential performance characteristics: it stores canonical DTO references, exposes index-to-identity access, and uses one `beginResetModel()`/`endResetModel()` batch replacement instead of per-item widgets.

The smallest new presentation contract is `ContentType` (`LIVE`, `MOVIE`, `SERIES`, `EPISODE`) plus immutable `ContentItemDTO`. It is a presentation projection, not a replacement domain entity. It preserves stable item/provider identity and contains content-appropriate optional data such as `stream_id`, category, poster URL, year, rating, plot, series ID, season, and episode number. `ChannelDTO` stays distinct, protecting the specific live semantics of channel number, live stream identity, and channel category.

| New abstraction | Responsibility | Why it is minimal |
|---|---|---|
| `ContentType` | Names the UI’s content-family context | Makes Live/Movie/Series/Episode state explicit without changing domain objects |
| `ContentItemDTO` | Safe immutable Movie/Series/Episode-oriented projection | Avoids corrupting `ChannelDTO`; preserves identity and metadata required by catalogue/detail UI |
| `ProviderContentResolverPort` | Optional resolver seam for VOD, Series, and capability declarations | Reuses the existing registered runtime provider rather than duplicating provider logic or expanding legacy live fakes |
| `BrowseContent` | Maps existing `Movie`/`Series` entities to `ContentItemDTO` | Adds only application orchestration that was absent |
| `LoadProviderCapabilities` | Maps runtime `ProviderCapability` values to existing safe booleans | Drives navigation from actual executable capability declarations |
| `ContentListModel` | Batched, virtualized-model-style Movie/Series rendering | Retains scalable Qt model/view behavior without altering the Live model |

## Implementation details

### Provider-capability-driven navigation

`PlayerShell` now rebuilds its navigation entries from the selected provider’s runtime capability summary. Live TV appears only when `LIVE` is declared; Movies appears only for `VOD`; Series only for `SERIES`; and EPG only for `EPG`. Favorites, History, Providers, and Settings remain existing application workflows. Unsupported capability domains are not promoted into active primary navigation.

The provider selector itself, its editable fallback behavior, existing dialogs, menus, and safe provider list remain intact. On a provider change, the shell clears only presentation-local content snapshots and category selector state, preserves the current live player state model, and uses the existing request-generation approach to prevent stale work from becoming visible.

### Content catalogue, category, and search semantics

Movie and Series catalogues are loaded only by an explicit user action. `BrowseContent` reuses `VodProvider.load_movies()` and `SeriesProvider.load_series()` through the registered provider resolver. It creates no competing provider implementation and writes no second application cache. After explicit load, the `PlayerShell` retains the same kind of local presentation snapshot already used for loaded live data; title, genre/category, and year filtering occurs locally.

For Live TV, the existing `ChannelCatalogueCache` and `SearchRegisteredChannels` cache-first behavior remains authoritative and unchanged. For Movies and Series, header search is local over the explicitly loaded snapshot and therefore causes no provider search, resolver, or catalogue reload call on a keystroke. Clearing the query restores the local snapshot. The existing category use case now accepts an optional content family with `LIVE` as the default, so all legacy callers preserve their live-category behavior while Movies and Series can use existing VOD/series category provider methods after an explicit content load.

| Content family | Search fields implemented | Network behavior |
|---|---|---|
| Live TV | Existing channel name/cache-first logic; local category filter | Preserved cache-first boundary; no new cache |
| Movies | Title, category/genre label, category ID, year | Local only after explicit catalogue load |
| Series | Title, category/genre label, category ID, year | Local only after explicit catalogue load |
| Episodes | No provider loader is currently exposed | Explicitly unavailable; no fabricated backend behavior |

### Player and activation semantics

The Phase 6 invariant **selected is not playing** remains unchanged for Live TV. A selected channel does not resolve or start a stream; Enter and double-click remain explicit live playback actions using a synchronously captured immutable `ChannelDTO`.

Movie selection likewise does not start playback. Explicit Movie activation opens the movie’s safe local context and accurately states that VOD playback is not yet exposed by the current provider/application stream-resolution boundary. The UI does not bypass that boundary or construct a stream URL. Series selection and explicit activation show safe detail context and accurately state that episode browsing is unavailable because no existing episode loader is exposed. This is intentionally capability-honest: the UI does not present playback, seasons, or episodes as completed workflows when the necessary application contracts do not yet exist.

Movie and Series lists support mouse selection, double-click activation, keyboard Up/Down selection context, and Enter activation. These interactions share the model-backed design and do not start live playback.

## Exact files changed

The following table includes preserved Phase 6 changes and the content-aware evolution. `UI_REDESIGN_IMPLEMENTATION_REPORT.md` remains the one consolidated report.

| Area | Files |
|---|---|
| Application DTOs | `src/samotech_iptv/application/dtos.py`; `application/dtos/__init__.py`; `application/dtos/categories.py`; **new** `application/dtos/content.py` |
| Application ports/use cases | `application/ports/__init__.py`; **new** `application/ports/provider_content_resolver_port.py`; `application/use_cases/load_categories.py`; **new** `application/use_cases/browse_content.py`; **new** `application/use_cases/load_provider_capabilities.py` |
| Composition/resolution | `desktop_bootstrap.py`; `desktop_composition.py`; `infrastructure/providers/provider_resolution_service.py` |
| Presentation | `presentation/player_shell.py`; `presentation/views/main_window.py`; **new** `presentation/viewmodels/content_list_model.py`; preserved Phase 6 `presentation/dialogs/channel_browser_dialog.py` |
| Tests and probes | `tests/player_shell_native_probe.py`; `tests/test_application_load_categories.py`; **new** `tests/test_application_browse_content.py`; **new** `tests/test_application_load_provider_capabilities.py`; preserved/extended **new** `tests/player_shell_performance_probe.py`; preserved/extended **new** `tests/test_presentation_01_player_shell_performance.py` |
| Documentation | `UI_REDESIGN_IMPLEMENTATION_REPORT.md` |

## Content-aware validation and performance results

The extended native offscreen Qt probe passed all original Phase 6 assertions plus the new provider-capability navigation and Movie/Series interactions. The probe confirms that selected Movie identity remains canonical, local Movie search does not trigger another content load, and keyboard Movie activation does not invoke the live `play_registered_channel` path.

| Native Qt assertion | Result |
|---|---|
| Existing stale identity protection | PASS |
| Existing legacy dialog stale identity protection | PASS |
| Existing selection without live playback | PASS |
| Existing local live category filtering | PASS |
| Existing keyboard accessibility | PASS |
| Runtime capability navigation | PASS |
| Movie/Series content identity and local search | PASS |
| Keyboard Movie activation without live playback | PASS |

The exact live stress test still operates on **39,753** records. Its latest local offscreen execution preserved first/middle/last identity as `channel-00001`, `channel-19877`, and `channel-39753`, selected the same middle channel, replaced the live model in a single batch, and issued zero resolver, provider-search, and catalogue-reload calls during cache-first search scenarios. A bounded non-live model check adds 5,000 mixed Movie/Series `ContentItemDTO` records and preserves `content-00001`, `content-02501`, and `content-05000` identity.

| Operation | Latest local offscreen measurement |
|---|---:|
| Live model replacement, 39,753 records | 0.198 ms |
| Live selection latency | 0.030 ms |
| Live empty replacement | 0.073 ms |
| Live filtered-result replacement | 1.392 ms |
| Cache-first common live search | 1.242 ms |
| Cache-first no-match live search | 1.025 ms |
| Clear live search | 0.006 ms |
| New `ContentListModel` replacement, 5,000 mixed Movie/Series records | 0.015 ms |
| Resolver calls during cache-first live search | 0 |
| Provider-search calls during cache-first live search | 0 |
| Catalogue reload calls during cache-first live search | 0 |

These are local, offscreen validation measurements and not end-user performance guarantees. They demonstrate that the implementation has not hard-coded a catalogue size, regressed the validated large live path, or introduced per-item Qt widgets.

## Full regression and quality results

The complete suite was re-run after resolving all task-introduced static diagnostics. It collected **688 tests** and completed successfully with no test failures. The run retained four existing `aiohttp` deprecation warnings about bare handlers in HTTP-session lifecycle tests; they are warnings only and not task regressions.

| Gate | Result | Classification |
|---|---|---|
| Full `pytest` with `QT_QPA_PLATFORM=offscreen` | **688 tests collected; full run passed with 0 failures** | Pass |
| Extended native Qt probe | **PASS** | Pass |
| Extended live/non-live performance probe | **PASS** | Pass |
| `black --check src tests` | **PASS**; 297 files unchanged | Pass |
| `ruff check src tests` | **PASS** | Pass |
| `git diff --check` | **PASS** | Pass |
| `mypy src` | 11 errors in 4 files | Pre-existing baseline only |

The initial content-aware type check surfaced six task-introduced diagnostics: four PySide override/import diagnostics in the new `ContentListModel` and two provider-variable typing diagnostics in `BrowseContent`. Those were corrected. The final mypy output is again the same 11 inherited diagnostics in `channel_list_model.py`, `history_library_dialog.py`, `favorites_library_dialog.py`, and `main_window.py`; no new content-aware file appears in the final mypy error set.

## Security and scope review

The new application code stays on the safe side of existing boundaries. `BrowseContent` calls only already defined provider capability interfaces and maps canonical domain entities to safe DTOs. `LoadProviderCapabilities` reads only the existing runtime capability declaration. No code reads or exposes credentials, MAC addresses, tokens, session values, raw provider payloads, resolved stream URLs, or provider-specific transport details.

`ProviderResolutionService` was extended only as the existing composition/resolution seam for the already implemented `VodProvider`, `SeriesProvider`, and `CapabilityProvider` interfaces. No provider adapter, MAG flow, M3U flow, Xtream transport, HTTP client, stream resolver, VLC adapter, or player internals were changed.

| Explicitly protected area | Final result |
|---|---|
| MAG authentication, MAC identity, handshake, session, and transport | Untouched |
| M3U and Xtream protocol/transport behavior | Untouched |
| Provider adapters and credentials | Untouched |
| Stream resolution and VLC/player internals | Untouched |
| Persistence, Favorites/History repositories, and deployment/CI configuration | Untouched |
| Generated logs, benchmark output, and temporary artifacts | Not included in the working tree |

## Remaining limitations and recommended next steps

The architecture now understands `EPISODE`, but the existing provider/application architecture does not expose an episode loader, season loader, VOD stream resolver, or episode stream resolver. Accordingly, Series opens safe context rather than a fabricated season/episode workflow, and Movie activation opens safe context rather than attempting playback. A future, separately approved increment should add only the missing capability contracts and registered-provider use cases required for episode retrieval and VOD/episode playback; it should retain the current content DTO and model/view presentation strategy.

The existing live `SearchProvider` remains channel-oriented. Movies and Series therefore search locally after explicit browse, which satisfies the no-provider-call-on-keystroke requirement but does not offer server-side VOD/series search. If future providers expose typed VOD/series search capabilities, they should be integrated through a deliberate application-level cache/boundary design rather than by adding a second competing cache inside presentation code.

Manual acceptance testing should use a representative capability-rich Xtream provider and a live-only MAG or M3U provider. Confirm that the first shows only its declared Movies/Series/EPG sections, while the second does not expose unsupported primary content sections. Then confirm Live selection does not play, explicit live activation does play, Movie selection/search/filtering remains local, and Movie activation does not bypass the current playback boundary.

## Final Git status and handoff

The repository remains on `HEAD` `98326ceec5ddb83d7679f6ff93696fa7e8d53e43`. The working tree is intentionally uncommitted for review. There was **no commit and no push**. The preserved Phase 6 changes remain alongside the content-aware evolution.

| Status group | Files |
|---|---|
| Modified tracked files | `application/dtos.py`; `application/dtos/__init__.py`; `application/dtos/categories.py`; `application/ports/__init__.py`; `application/use_cases/load_categories.py`; `desktop_bootstrap.py`; `desktop_composition.py`; `infrastructure/providers/provider_resolution_service.py`; Phase 6 `presentation/dialogs/channel_browser_dialog.py`; `presentation/player_shell.py`; `presentation/views/main_window.py`; Phase 6 `tests/player_shell_native_probe.py`; `tests/test_application_load_categories.py` |
| New untracked files | This consolidated report; `application/dtos/content.py`; `application/ports/provider_content_resolver_port.py`; `application/use_cases/browse_content.py`; `application/use_cases/load_provider_capabilities.py`; `presentation/viewmodels/content_list_model.py`; Phase 6 `tests/player_shell_performance_probe.py`; `tests/test_application_browse_content.py`; `tests/test_application_load_provider_capabilities.py`; Phase 6 `tests/test_presentation_01_player_shell_performance.py` |
| Baseline | `98326ceec5ddb83d7679f6ff93696fa7e8d53e43` |
| Commit / push | Not performed; explicit approval required |

---

# Forensic Integration Audit Addendum

**Status at this point:** all required safety, provider, architecture, dynamic-scale, native Qt, regression, and quality checks have passed. The report will be updated with the final commit and normal-push evidence after the requested staging review is complete.

## Preservation snapshot

The required pre-audit snapshot confirmed branch `main` at `98326ceec5ddb83d7679f6ff93696fa7e8d53e43`, with `origin/main` pointing to that same baseline. The complete Phase 6 and content-aware working tree was present before any audit adjustment. No reset, hard reset, clean, checkout-discard, restore, stash, revert, rebase, force-push, or destructive deletion was used.

## Provider and architecture forensic result

The audit compared the working tree with the baseline for MAG, M3U, Xtream, VLC/player, stream-resolution, and cache/search files. The following protected files are unchanged: `mag_adapter.py`, `m3u_adapter.py`, `xtream_adapter.py`, `vlc_player_adapter.py`, `vlc_video_surface.py`, `play_registered_channel.py`, `search_registered_channels.py`, and `channel_catalogue_cache.py`.

`ProviderResolutionService` is the sole infrastructure-resolution file changed by the content-aware pass. Its added methods call its existing `_resolve()` composition/runtime path and type-check only already declared `VodProvider`, `SeriesProvider`, and `CapabilityProvider` interfaces. The diff contains no adapter mutation, request construction, session operation, authentication flow, MAC handling, portal discovery, pagination, payload translation, stream resolution, or transport behavior.

| Audit area | Result |
|---|---|
| MAG authentication, MAC, handshake, portal discovery, catalogue, pagination, and live stream resolution | Unchanged |
| M3U playlist load/parsing, category handling, stream URLs, and playback behavior | Unchanged |
| Xtream authentication, live/VOD/series catalogue behavior, categories, sessions, and stream resolution | Unchanged |
| VLC adapter, native video surface, output attachment, play/pause/stop | Unchanged |
| `ProviderResolutionService` | Capability/composition resolution only; no provider protocol behavior added or changed |
| `PlayerShell` | Invokes supplied use cases only; no stream resolution, provider-client construction, credentials, or protocol implementation |
| `BrowseContent` | Reuses existing VOD/Series capability interfaces and projects safe DTOs only |
| Cache/search | `ChannelCatalogueCache` and `SearchRegisteredChannels` unchanged and remain the authoritative cache-first Live boundary |

The production source tree contains no hard-coded `39,753`, `39_753`, `100,000`, or `100_000` catalogue-size value. The values appear only in the stress probe and test wrapper. Both `ChannelListModel` and `ContentListModel` are `QAbstractListModel` implementations and replace collections with one `beginResetModel()`/`endResetModel()` pair. The new catalogue path creates no `QListWidgetItem` or row widget.

## Audit finding fixed during this pass

One real presentation-layer race was found and corrected before validation: `load_content()` checked the request generation before awaiting non-live category loading but did not re-check it after that await. A provider change while Movie/Series category loading was delayed could therefore let the old request continue to render stale content after the provider context changed.

The fix captures `provider_id` at content-load start, passes it with the request generation into `refresh_content_categories()`, and re-checks both values after the await before rendering or changing status. The shared search field now also changes its placeholder and accessible name between Live TV, Movies, and Series, clarifying the current content context without redesigning the application. The native Qt probe includes `content_stale_provider_protection=PASS`, which exercises this provider-change-during-category-load sequence.

While expanding the dynamic probe, the test initially reused the same shell state after the exact 39,753 assertion and thereby overwrote the original selected-channel identity. This was a probe-only regression, not production behavior. It was corrected by capturing the original selection identity before the dynamic loop; the final probe and full suite pass.

## Dynamic catalogue validation

The extended offscreen probe validated dynamic Live catalogues of 0, 1, 100, 1,000, 5,000, 39,753, and 100,000 records. Every size correctly restored all rows after a local-query clear, kept category-filter rows bounded by the current catalogue, and retained canonical selected identity when an item existed. The 100,000-record case is a test-only synthetic stress check; no product limit was introduced.

| Live records | Model replacement | Selection | Local category filter | Local search render | Clear restores |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.006 ms | n/a | 0.120 ms | 0.002 ms | 0 |
| 1 | 0.001 ms | 0.014 ms | 0.003 ms | 0.002 ms | 1 |
| 100 | 0.002 ms | 0.005 ms | 0.007 ms | 0.002 ms | 100 |
| 1,000 | 0.003 ms | 0.006 ms | 0.040 ms | 0.002 ms | 1,000 |
| 5,000 | 0.007 ms | 0.008 ms | 0.200 ms | 0.006 ms | 5,000 |
| 39,753 | 0.090 ms | 0.020 ms | 1.374 ms | 0.030 ms | 39,753 |
| 100,000 | 0.431 ms | 0.051 ms | 4.931 ms | 0.084 ms | 100,000 |

The final exact-39,753 run also reported 0.170 ms for initial live-model replacement, 0.030 ms for selection, 1.560 ms for filtered-result replacement, 0.017 ms for the 5,000-item Movie/Series model replacement, and zero resolver, provider-search, and catalogue-reload calls on the cache-first Live search path. These values are local offscreen validation measurements rather than end-user performance guarantees.

## Final validation before staging

| Gate | Result |
|---|---|
| Full offscreen pytest | **688 tests collected; full run passed with 0 failures** |
| Native PySide6 probe | **PASS**, including Live/Movie/Series capability navigation, local filtering, async identity, and provider-change protection |
| Exact 39,753 + dynamic 0-to-100,000 performance probe | **PASS** |
| Black | **PASS**; 297 source/test files unchanged |
| Ruff | **PASS** |
| `git diff --check` | **PASS** |
| Mypy | 11 diagnostics in 4 baseline files only; no task-introduced diagnostic remains |

The four inherited `aiohttp` bare-handler deprecation warnings remain warnings only. They did not cause test failures and were not changed in this task.

---

# Real-Provider Acceptance and Forensic Validation Addendum

## 1. Acceptance baseline

The acceptance pass began from the already committed, synchronized baseline `d4f3edf4003c86f73f78192142b3012e94ab2755` on `main`. At the start of the pass, `HEAD`, `origin/main`, and the remote `main` reference matched, and the implementation working tree was clean. The temporary `todo.md` created only to track this pass is not an implementation artifact and will be removed before handoff.

The previous player-first guarantees remain present. Live uses `ChannelListModel`; Movies and Series use `ContentListModel`; both are `QAbstractListModel`-based and rendered through `QListView` rather than per-row widgets. `ChannelDTO` and `ContentItemDTO` remain immutable projections; selected Live state is distinct from loading, playing, and playback-error state; Live activation remains explicit; non-live activation does not enter Live playback; runtime capability declarations gate navigation; and no production catalogue-size limit exists.

| Required architectural guarantee | Classification | Evidence |
|---|---|---|
| Scalable Live and non-live catalogues | **PASS** | Batched Qt model resets; no `QListWidget`, `QListWidgetItem`, or row widget in the catalogue paths. |
| Selection is separate from playback | **PASS** | Native probe verifies selection alone has no playback side effect; Enter/double-click performs explicit activation. |
| Capability-driven navigation | **PASS** | Runtime `ProviderCapabilities` determines Live, Movies, Series, and EPG navigation visibility. |
| Cache-first Live search; local non-live search | **PASS** | Cache probe records zero resolver/provider-search/reload calls; Movie/Series filter the loaded local snapshot. |
| Stale async and provider-change protection | **PASS** | Direct native races cover Live, Movie, Series, categories, search, and playback state. |
| No fixed catalogue-size assumption | **PASS** | Dynamic test covers 0, 1, 10, 100, 500, 1,000, 5,000, 17,431, 39,753, and 100,000 records. |

## 2. Lawful public test data and provider capability matrix

The Internet data check was intentionally limited to published test/reference material and metadata parsing. No user credentials, paid provider accounts, private portal endpoints, MAC identities, MAG handshakes, stream resolutions, or media playback requests were used. The [iptv-org repository][1] publishes its playlist URL and states that it contains links to publicly available streams rather than video files; it was therefore used only as a parser/capability reference, not as an endorsement or replay source. The published [Xtream mock API][2] was queried only through its documented test account and only for response-family counts. No official anonymous Stalker/MAG sandbox suitable for this application’s credential/MAC model was identified, so no Stalker portal was contacted.

| Source or provider | Live | VOD | Series | Episodes | Categories | Search | EPG | Playback | Classification and notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| MAG/Stalker adapter | Yes | No | No | No | No typed `CategoryProvider` | Yes | Yes | Live only | **PASS** for actual declared runtime scope. It exposes authentication, session, Live, EPG, search, and stream resolution—not VOD/Series. |
| M3U adapter | Yes | No | No | No | Channel metadata only; no typed category loader | Yes | No | Live only | **PASS** for declared scope. It exposes Live, search, and stream resolution. |
| Xtream adapter | Yes | Yes | Yes | No loader | Yes, all three families | Yes | Yes | Live only at the application playback boundary | **PASS** for catalogue/navigation scope. Movie/episode stream resolution is not implemented. |
| Public iptv-org M3U reference | Live metadata | n/a | n/a | n/a | Parsed group-title metadata | n/a | Playlist EPG URL may exist | Not attempted | **PASS** for HTTP(S) parser subset; see compatibility limitation below. |
| Published Xtream mock API | 2 streams | 3 VOD categories | 1 series | API sample only | 3 Live, 3 VOD, 1 Series categories | API sample only | Not tested | Not attempted | **PASS** for read-only multi-family mock metadata; no real media was requested. |
| Public Stalker/MAG endpoint | Not used | Not used | Not used | Not used | Not used | Not used | Not used | Not used | **BLOCKED**. No safe anonymous test portal was found; using arbitrary portals or MAC identities would be inappropriate. |

The provider matrix is derived from executable adapter declarations and port interfaces, not from provider names. It therefore avoids assuming that every MAG/Stalker installation exposes a fixed VOD/Series model. In the current application, a MAG provider will show only the workflows its actual runtime declaration supports.

## 3. Public M3U acceptance and bug fixed

The documented public M3U reference returned `200 OK` as `audio/x-mpegurl`. A metadata-only parse initially found two independent compatibility facts. First, the full document contains `mmsh://` at line 17,977, which is outside the current canonical `StreamTransport` set; a full import is therefore **BLOCKED** rather than silently misrepresenting or playing that transport. Second, HTTP(S) entries whose quoted `http-user-agent` metadata contained commas were parsed incorrectly: the parser treated the comma inside the quoted value as the title separator.

The quoted-comma behavior was a demonstrated parser defect, not a provider-transport change. It was fixed in `M3UParser` by locating the first comma outside quoted attribute values and covered with a deterministic regression test. The post-fix HTTP(S) metadata subset parsed **12,726 channels**, **12,726 streams**, and **175 categories**; the previously malformed titles and group categories now project correctly. No playlist was registered, stored, streamed, or played.

| Public M3U result | Classification | Result |
|---|---|---|
| Source availability and response type | **PASS** | `200 OK`, `audio/x-mpegurl`. |
| Quoted-comma `#EXTINF` metadata | **PASS after fix** | Title, `group-title`, and ID preserved when quoted HTTP-header metadata contains commas. |
| HTTP(S) parser subset | **PASS** | 12,726 accepted metadata entries, no media playback. |
| Full mixed-transport playlist | **BLOCKED** | `mmsh://` is not represented by the current transport value object; no protocol expansion was attempted. |

## 4. Isolated provider simulation, content behavior, and race results

The acceptance suite remains isolated from production provider accounts. The native Qt probe supplies fakes at existing use-case boundaries and verifies that each presentation state is honest. The dynamic performance probe supplies model data only and performs no row-level network work.

| Acceptance case | Classification | Result |
|---|---|---|
| A: small Live provider, 10 channels | **PASS** | Identity, selection, category, local search, no-match, and clear-search results validated. |
| B: medium Live provider, 500 channels | **PASS** | Same dynamic assertions; clear restores all 500 rows. |
| C: large Live provider, 39,753 channels | **PASS** | First/middle/last identity is `channel-00001` / `channel-19877` / `channel-39753`. |
| D: very large Live provider, 100,000 channels | **PASS** | Batched replacement, filtering, search, no-match, selection, and clear all completed without a fixed-size branch. |
| E: Live + VOD | **PASS** | Explicit Movie load, category filter, year/title local search, selection, and Enter context are supported; Live playback is not invoked. |
| F: Live + VOD + Series | **PASS** | Capability-rich navigation exposes both Movies and Series; Series opens an honest unsupported-episode context. |
| G: Live-only MAG/M3U-style capability set | **PASS** | Live is present while Movies and Series are absent. |
| H: capability-rich Xtream-style set | **PASS** | Live, Movies, and Series appear only after runtime capability loading. |
| Episodes | **BLOCKED, honest** | No season/episode loader or episode playback resolver exists; the UI does not fabricate either. |

Provider-switch races were directly tested as `A → B` transitions. Late Live-load, Movie-load, Series-load, category-load, search, and playback completions do not render A data or playing state under B. The native probe also keeps existing request-generation protection for same-provider stale searches. The generic implementation means the same generation/provider guard is applied to B → A transitions as well; no unsupported re-authentication or protocol behavior was introduced.

| Content or player interaction | Classification | Result |
|---|---|---|
| Live categories, local filtering, query and clear | **PASS** | Local model rendering only after catalogue availability. |
| Live selection, keyboard arrows, Enter, double-click | **PASS** | Selection does not play; explicit activation schedules existing Live playback boundary. |
| Movie explicit load, category and title/year search | **PASS** | Local `ContentListModel` filtering; no provider call per keystroke. |
| Movie Enter/double-click | **PASS, honest** | Opens VOD context and explicitly reports that VOD playback is not exposed. |
| Series explicit load, category/title search, selection | **PASS** | Opens Series context without inventing episodes or playback. |
| Search-context clarity | **PASS** | Shared control changes placeholder and accessible name for Live, Movies, and Series. |
| Selected, loading, playing, and error labels | **PASS** | Distinct PlayerShell state and label paths remain present. |
| Provider-switch playback state | **PASS after fix** | A late prior-provider playback completion can no longer restore stale `playing_channel` state. |

## 5. Dynamic catalogue and performance results

All dynamic sizes asserted first/middle/last identity when non-empty, current selection identity, local category filtering, local search, no-match result, and clear-search restoration. The results below are local offscreen measurements, not end-user performance guarantees.

| Records | Model replacement | Selection | Category filter | Search render | No-match | Clear restore |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.012 ms | n/a | 0.150 ms | 0.002 ms | 0.002 ms | 0 |
| 10 | 0.001 ms | 0.005 ms | 0.004 ms | 0.002 ms | 0.002 ms | 10 |
| 500 | 0.003 ms | 0.008 ms | 0.021 ms | 0.002 ms | 0.002 ms | 500 |
| 17,431 | 0.077 ms | 0.021 ms | 0.661 ms | 0.013 ms | 0.004 ms | 17,431 |
| 39,753 | 0.182 ms | 0.046 ms | 2.021 ms | 0.031 ms | 0.008 ms | 39,753 |
| 100,000 | 0.353 ms | 0.058 ms | 4.717 ms | 0.088 ms | 0.027 ms | 100,000 |

The exact 39,753-record cache-first probe measured 0.196 ms initial model replacement, 0.030 ms selection, 1.470 ms filtered-result replacement, and 0.020 ms 5,000-item content-model replacement. Empty, common, rare, no-match, repeated, and clear search requests reported zero resolver calls, zero provider search calls, and zero catalogue reload calls.

## 6. Final quality and regression evidence

| Gate | Classification | Result |
|---|---|---|
| Full `pytest` | **PASS** | **689 tests collected; 0 failures**. |
| Native Qt/offscreen probe | **PASS** | Live, Movie, Series, capabilities, keyboard behavior, stale identity, and all provider-switch races pass. |
| Dynamic 0-to-100,000 performance probe | **PASS** | Includes 10, 500, and 17,431 acceptance cases. |
| Black | **PASS** | 297 source/test files would remain unchanged. |
| Ruff | **PASS** | No diagnostics. |
| `git diff --check` | **PASS** | No whitespace diagnostics. |
| Mypy | **INHERITED** | 11 diagnostics in 4 pre-existing files only; no acceptance-pass source file appears in the result. |
| Warnings | **INHERITED** | Four `aiohttp` bare-handler deprecation warnings; no test failure. |

## 7. Evidence-based IPTV player gap analysis

The following items are gaps evidenced by current source/UI behavior. They are not implemented by this acceptance pass.

| Priority | Gap | Evidence and decision |
|---|---|---|
| P0 | None identified | Core Live browse, explicit activation, capability navigation, and stale-state behavior pass the acceptance suite. |
| P1 | Episode/season browsing and VOD/episode playback | Existing content DTO declares `EPISODE`, but no loader, season flow, or VOD/episode stream resolver exists. Keep the current honest UI until a separate provider/application contract change is approved. |
| P1 | M3U mixed-transport compatibility | The public reference includes unsupported `mmsh://`; the current domain rejects the complete playlist. A future design must decide whether to skip unsupported entries or support additional transports without weakening validation. |
| P1 | Channel next/previous, numeric entry, volume/mute, and subtitle/audio controls | No corresponding PlayerShell controls or keyboard paths were found. These require product and player-port design, not a presentation-only patch. |
| P2 | M3U category navigation from parsed metadata | M3U channels retain `group-title`, but the adapter does not expose typed category loading; the persistent selector therefore has no provider category API for M3U. |
| P2 | Movie/Series poster and rich metadata presentation | `ContentItemDTO` preserves poster/plot/rating/year, but the current list renders title/year/rating text only. |
| P2 | EPG interaction depth | Capability-driven EPG navigation exists, but this acceptance pass did not establish programme-grid or programme-action parity with a mature desktop IPTV player. |
| P3 | Remote-control style focus/shortcut polish and responsive-detail refinements | Arrow, Enter, F, and Escape behavior is covered; broader remote-style mappings and visual polish require user-experience decisions. |

## 8. Scope, security, and uncommitted handoff

The only production changes in this acceptance pass are a quote-aware `#EXTINF` separator in `m3u_parser.py` and provider-generation protection around the presentation playback result in `player_shell.py`. Neither change alters MAG/Stalker authentication, MAC handling, portal transport, M3U source registration, Xtream transport, credential storage, stream URL construction, or VLC internals. The remaining changes are isolated tests/probes and this report.

| Final handoff field | Value at report preparation |
|---|---|
| Current HEAD | `d4f3edf4003c86f73f78192142b3012e94ab2755` |
| Origin/main | `d4f3edf4003c86f73f78192142b3012e94ab2755` |
| Working tree | Intentionally uncommitted acceptance fixes and report only; no commit or push performed. |
| Files changed | `UI_REDESIGN_IMPLEMENTATION_REPORT.md`; `src/samotech_iptv/infrastructure/parsing/m3u_parser.py`; `src/samotech_iptv/presentation/player_shell.py`; `tests/test_infra_b2_m3u_parser.py`; `tests/player_shell_native_probe.py`; `tests/player_shell_performance_probe.py`; `tests/test_presentation_01_player_shell_performance.py`. |
| Files intentionally untouched | MAG/Stalker adapter and protocol, MAC/credential/session code, M3U adapter/source registration, Xtream adapter/transport, stream resolution, VLC/player internals, deployment/CI configuration, persistence implementation. |
| Bugs found | Quoted-comma M3U EXTINF parsing; stale playback state after provider switch; full public playlist transport incompatibility. |
| Bugs fixed | Quote-aware EXTINF split; stale playback result guard. |
| Remaining P0 | None identified. |
| Remaining P1 | Episodes/VOD playback, mixed M3U transport decision, richer player transport controls. |
| Remaining P2 | M3U category API, poster/metadata UI, deeper EPG workflow. |
| Recommended next step | Obtain a licensed provider test account or an organisation-owned local Xtream/Stalker fixture, then approve a separately scoped application-contract increment for episode/VOD playback and any supported transport expansion. |

## References

[1]: https://github.com/iptv-org/iptv "iptv-org public IPTV playlist repository"
[2]: https://github.com/j2jstudio/xtream-codes-mock-api "Published Xtream mock API documentation"

## 9. Phase 7A — Unified Content Playback Contract

### 9.1 Objective and scope boundary

Phase 7A introduces one small **application-layer playback contract** that makes the requested content identity explicit and protects Live playback from stale same-provider completions. It does not implement VOD, series details, seasons, episodes, episode playback, player controls, provider changes, or visual redesign. The pre-existing `PlayerPort.play(URL)` signature remains unchanged, and provider adapters continue to own all real stream resolution.

> **Safety invariant:** Presentation and application orchestration carry a provider-scoped content identity, never credentials, MAC addresses, tokens, session material, or raw resolved stream URLs.

### 9.2 Architecture and contract design

The new contract lives between presentation activation and the existing provider resolver/player ports. `PlayerShell` creates a `PlaybackTarget` from the selected Live channel and sends it through `MainWindow` to `PlayRegisteredChannel.execute_target()`. The legacy `PlayRegisteredChannel.execute(provider_id, channel_id)` remains available for dialog compatibility, but now delegates to the same target use case. The unified use case resolves only supported Live targets through the existing `ProviderResolverPort`, converts the canonical ID to the existing domain `ChannelId`, and calls the unchanged `PlayerPort.play(URL)` only when the attempt is still current.

| Contract element | Design | Security and compatibility effect |
|---|---|---|
| `PlaybackTarget` | Frozen provider-scoped dataclass with `provider_id`, `content_type`, `canonical_content_id`, optional `resource_id`, plus future episode identity fields. | Immutable and hashable. It contains no raw resolved URL or provider secret. |
| Validation | Supports only `LIVE`, `MOVIE`, and `EPISODE` identity types. Live requires an internal resource ID; episode identity requires parent series, season, and episode number. | Rejects malformed or ambiguous requests before orchestration. `SERIES` is intentionally not playable. |
| `PlaybackResult` | Immutable `PlaybackAttempt` plus `PLAYED`, `STALE`, `UNSUPPORTED`, or `FAILED`, with only generic safe error text. | A late resolver result becomes an explicit no-op rather than an uncontrolled player/UI update. |
| `PlaybackAttemptRegistry` | One monotonic integer generation and only the current attempt in memory. `begin()` replaces the current attempt; `invalidate()` advances generation and clears it. | O(1) state and comparison cost; no unbounded request history. |
| `PlayPlaybackTarget` | One Live-only application use case that checks generation after resolution, after player invocation, and before history recording. | Preserves current Live resolver/player boundaries while preventing stale result promotion. |
| Presentation wiring | Provider changes and explicit stop operations invalidate pending target resolution through a narrowly injected callback. | A pending earlier-provider completion cannot restore a stale visible playing state. |

### 9.3 Live behavior and explicit non-Live limitation

The existing Live path remains functionally compatible: registered provider lookup, domain `ChannelId` conversion, provider stream resolution, `PlayerPort.play(URL)`, and successful channel history recording retain their established order. Legacy calls still raise `ProviderError` for a failed Live start. The target-facing interface instead returns safe results so `PlayerShell` can leave stale results visually unchanged and display only generic failure feedback.

Movie and episode identities are intentionally represented but not executable in this increment. A Movie target returns `UNSUPPORTED` without resolving a provider or invoking the player. Series is rejected as an invalid playback target because it is a browsable container, not a playable media item. This is deliberate scope containment, not partial VOD implementation.

### 9.4 Files changed

| File | Change |
|---|---|
| `src/samotech_iptv/application/dtos/playback.py` | **New.** Immutable target, attempt, outcome, and result DTOs with validation. |
| `src/samotech_iptv/application/use_cases/play_playback_target.py` | **New.** Attempt registry and generation-safe Live orchestration use case. |
| `src/samotech_iptv/application/dtos/__init__.py` | Exposes the new public playback DTOs. |
| `src/samotech_iptv/application/dtos.py` | Exposes the same DTOs through the legacy compatibility shim. |
| `src/samotech_iptv/application/use_cases/__init__.py` | Exposes `PlayPlaybackTarget` and `PlaybackAttemptRegistry`. |
| `src/samotech_iptv/application/use_cases/play_registered_channel.py` | Preserves the legacy Live API while delegating through the unified target path; adds explicit invalidation. |
| `src/samotech_iptv/presentation/views/main_window.py` | Routes PlayerShell activation through `PlaybackTarget`; invalidates pending resolution on stop. |
| `src/samotech_iptv/presentation/player_shell.py` | Constructs a Live target, handles `PLAYED`/`STALE`/`FAILED`/`UNSUPPORTED`, and invalidates on provider switch. |
| `tests/test_application_play_playback_target.py` | **New.** Twenty deterministic application-contract and race tests. |
| `tests/player_shell_native_probe.py` | Updates the target callback and adds native assertions for stale results and invalidation. |

### 9.5 Race, identity, error, and redaction coverage

The new deterministic test module adds **20 tests**. The following acceptance cases were directly controlled with pending resolver futures; no network or real provider credential is involved.

| # | Scenario | Expected result | Result |
|---:|---|---|---|
| 1 | A → B; B resolves before A | Only B reaches `PlayerPort.play`. | **PASS** |
| 2 | A → B; A resolves before B | A returns `STALE`; only B plays. | **PASS** |
| 3 | A → provider context switch; A resolves late | A returns `STALE`; no player mutation. | **PASS** |
| 4 | A with no competing request | A resolves, plays, and records history. | **PASS** |
| 5 | A → B; both resolutions fail | A is stale; only B reports generic `FAILED`. | **PASS** |
| 6 | Movie target | Returns `UNSUPPORTED`; no resolver or player call. | **PASS** |
| 7 | Same provider and canonical ID, different content types | Target identities remain distinct. | **PASS** |
| 8 | Same Movie ID, different providers | Target identities remain distinct. | **PASS** |
| Additional | Invalid identity fields, explicit raw-URL rejection, frozen dataclass, generation monotonicity, player failure redaction, and legacy history-failure semantics | Explicit safe behavior is preserved. | **PASS** |

The native offscreen Qt probe additionally verifies that a Live selection still passes a `PlaybackTarget`, a `STALE` result does not promote playing/error state, Movie and Series activation still do not start playback, and provider switching invokes pending-attempt invalidation. Existing Live selection, legacy dialog activation, keyboard navigation, provider switching, and stale request checks remain green.

### 9.6 Validation and quality evidence

| Gate | Result | Evidence |
|---|---|---|
| Focused unified playback tests | **PASS** | 23 focused application/infrastructure tests after integration. |
| Full `pytest` | **PASS** | **709 collected tests**, zero failures, completed in approximately 3 seconds with `QT_QPA_PLATFORM=offscreen`. |
| Native Qt/offscreen probe | **PASS** | All printed checks, including `playback_attempt_invalidation` and `playback_stale_result_protection`, passed. |
| Black | **PASS** | 300 source/test files would remain unchanged. |
| Ruff | **PASS** | No diagnostics in `src` or `tests`. |
| Changed-module mypy | **PASS** | The three new/modified application playback modules pass strict checking. |
| Full-repository mypy | **INHERITED** | 11 existing PySide annotation diagnostics in four files. Three are pre-existing unused-ignore annotations in `main_window.py`; the remaining diagnostics are in unrelated dialogs/viewmodels. No new application playback diagnostic remains. |
| `git diff --check` | **PASS** | No whitespace diagnostics. |
| Performance review | **PASS** | Registry operations are constant-time and retain one current attempt; the complete suite remained approximately 3 seconds. |
| Test warnings | **INHERITED** | Four existing `aiohttp` bare-handler deprecation warnings; no failure. |

### 9.7 Protected-area and security review

The final path audit found no modified provider, infrastructure, MAG/Stalker, credential, authentication, transport, stream-resolution, VLC, or `PlayerPort` files. The modified production paths are limited to application DTO/use-case exports, the legacy Live adapter, and presentation wiring. A sensitive-marker scan found only the report's public references and clearly synthetic `example.invalid` URLs inside tests. Production target and use-case code contains no credential, token, password, MAC, cookie, authorization, or raw HTTP stream literal. `PlaybackTarget` now explicitly rejects a `resource_id` containing `://`, so a raw resolved stream URL cannot be persisted in the target contract. Resolved URLs remain local to the existing provider-to-player call; they are neither stored in `PlaybackTarget` nor returned in `PlaybackResult`.

| Protected concern | Verification |
|---|---|
| MAG/Stalker protocol, MAC, credentials, session, transport | **Untouched.** |
| Xtream and M3U provider adapters/source registration | **Untouched.** |
| Provider stream resolution implementation | **Untouched.** The new use case calls the existing capability through `ProviderResolverPort`. |
| VLC/player internals and `PlayerPort.play(URL)` | **Untouched.** |
| VOD/Series/Episode playback and detail workflows | **Not implemented.** Movie returns safe `UNSUPPORTED`; Series remains non-playable. |
| Volume, mute, subtitles, audio tracks, seek, queue, EPG redesign, visual redesign | **Untouched.** |

### 9.8 Remaining limitations and exact next step

The attempt registry prevents stale asynchronous resolution from being promoted after a newer selection, provider switch, or explicit stop. It cannot retroactively cancel a player call that has already crossed the unchanged `PlayerPort.play(URL)` boundary; that lower-level cancellation behavior remains intentionally out of scope. VOD and episode playback still require a separately approved design for provider-neutral movie and episode stream resolution, season/episode discovery, history semantics, and player behavior.

**Exact next step:** review this uncommitted Phase 7A diff. If approved, create one review commit containing only the files listed above; do not push until explicit user approval is also given.

### 9.9 Uncommitted handoff state

| Field | Value |
|---|---|
| Baseline | `b9e714ceb2ef31b7b0581d73fe226312d1c8fb47` (`origin/main`) |
| Working tree | Intentionally uncommitted Phase 7A implementation, tests, and this consolidated report. |
| Commit created | **No.** |
| Push performed | **No.** |
| Review readiness | Ready for requested diff review and approval decision. |

## 10. Phase 8 — VOD / Series / Episode Playback Architecture Audit

### 10.1 Actual baseline, instructions, and review scope

This Phase 8 review used the repository as the source of truth rather than relying on historical reports. The current branch is `main`, the local baseline is `0ace7b88a38abe0dc24f3abf48c7128bdb94a0ad` (`feat(playback): add unified content playback contract`), and `origin/main` remains `b9e714ceb2ef31b7b0581d73fe226312d1c8fb47`. The worktree was clean before this audit. The repository-local `CONTRIBUTING.md` was read first, together with `PROJECT_STATUS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `PRODUCT_GAP_ANALYSIS.md`, and `SECURITY.md`.

The bounded implementation in this phase deliberately fixes only strict typing and regression coverage. It does **not** add Movie/VOD playback, season discovery, episode discovery, episode playback, a provider-specific Xtream UI path, new provider URL construction, persistence changes, or changes to MAG, M3U, VLC, `PlayerPort.play(URL)`, authentication, transport, credentials, CI, or deployment.

### 10.2 Current execution paths

| Content family | Current executable path | Current stop-point |
|---|---|---|
| Live | Registered provider → `ProviderResolutionService` → `BrowseChannels` / `LoadChannels` → `ChannelDTO` → `ChannelListModel` → explicit PlayerShell activation → `PlaybackTarget.live()` → `PlayPlaybackTarget` → existing provider `resolve_stream(ChannelId)` → unchanged `PlayerPort.play(URL)` → history item type `channel`. | Implemented and generation-protected. |
| Movie | Registered `VodProvider` → `BrowseContent` → `ContentItemDTO` containing provider-scoped Movie ID and non-URL stream ID → `ContentListModel` → local selection/filtering. | Explicit activation displays safe unavailable text; no Movie resolver/player/history path exists. |
| Series | Registered `SeriesProvider` → `BrowseContent` → flat `ContentItemDTO` → `ContentListModel` → local selection/filtering. | Series is a non-playable container; explicit activation reports that Episode browsing is unavailable. |
| Episode | Validated domain `Episode` record and DTO fields exist. | No season/episode loader, provider resolver member, adapter method, mapper, UI hierarchy, or playback call exists. `BrowseContent` returns Episode as unsupported with zero provider calls. |

### 10.3 Provider capability forensic matrix

The matrix below records only concrete adapter methods and runtime capability declarations. It does not infer support from a provider name, generic URL-builder potential, or an abstract port.

| Capability | M3U | MAG/Stalker | Xtream |
|---|---|---|---|
| Live catalogue / local search / Live resolution | **Implemented** | **Implemented** | **Implemented** |
| Live categories | No typed category capability | **Implemented** | **Implemented** |
| VOD catalogue | Not implemented | Not implemented | **Implemented** through `load_movies()` |
| VOD categories | Not implemented | Not implemented | **Implemented** through `load_vod_categories()` |
| Series catalogue | Not implemented | Not implemented | **Implemented** through `load_series()` |
| Series categories | Not implemented | Not implemented | **Implemented** through `load_series_categories()` |
| Season discovery | Not implemented | Not implemented | Not implemented |
| Episode discovery | Not implemented | Not implemented | Not implemented |
| Movie stream resolution | Not implemented | Not implemented | Not implemented |
| Episode stream resolution | Not implemented | Not implemented | Not implemented |
| EPG | Not implemented | **Implemented** | **Implemented** |
| Catch-up | Not implemented | Not implemented | Not implemented |

Xtream is the only current provider with executable Movie and Series catalogue capabilities. Its concrete adapter, API client, and translator stop at category and flat-catalogue operations; its only stream resolver remains the Live `resolve_stream(ChannelId)` path. M3U and MAG/Stalker remain capability-limited Live paths and must not gain implied non-live behavior.

### 10.4 Playback contract assessment and minimal next architecture

`PlaybackTarget`, `PlaybackAttempt`, `PlaybackResult`, and `PlaybackAttemptRegistry` are suitable foundations for all future playable target identities. The target is frozen, provider-scoped, content-type-aware, and rejects `://` inside `resource_id`; resolved URLs therefore remain outside application DTOs. Series should remain non-playable. A Movie can be represented safely by provider-scoped canonical Movie ID plus its non-URL resource identity. An Episode can be represented safely by provider ID, canonical Episode ID, parent Series ID, season, episode number, and non-URL resource identity.

However, target identity alone does not create a resolution capability. The next architectural increment should introduce narrow provider-neutral interfaces—not presentation calls or Xtream-only code—for Movie playback, Series detail/season discovery, Episode discovery, and Episode playback. `ProviderResolutionService` should then resolve those interfaces from the registered runtime provider and return controlled unsupported errors where absent. The existing `PlayPlaybackTarget` should remain the one attempt-generation owner and eventually dispatch Live/Movie/Episode only through their respective narrow resolver interfaces; Series remains `UNSUPPORTED`.

| Proposed boundary | Minimum responsibility | Explicit exclusion |
|---|---|---|
| `MoviePlaybackProvider` | Resolve a canonical Movie/resource identity to `URL` inside infrastructure. | Does not expose raw URL to DTOs or UI. |
| `SeriesDetailProvider` | Load stable seasons and episodes for one canonical Series identity. | Does not resolve/play a stream. |
| `EpisodePlaybackProvider` | Resolve canonical Episode/resource identity to `URL` inside infrastructure. | Does not call Qt or libVLC directly. |
| Application use cases | Convert canonical records to safe DTOs, sanitize unsupported/error results, and preserve request context. | No provider API/credential/session access. |
| Presentation | Navigate Series → Season → Episode and create a target only upon explicit activation. | No provider-specific API access or implicit playback. |

There is no canonical `Season` domain entity today. Add one only if an authorized concrete provider supplies a stable season identity/order; otherwise begin with a small provider-neutral season DTO. The existing `Episode` record has valid season/episode/resource fields but does not itself carry provider ID, so the future provider-scoped application projection must supply it.

### 10.5 History and UI/UX recommendation

The current `History` record and `RecordHistoryRequest` already support a canonical `item_id`, `item_type`, timestamp, duration, and position. No schema change is needed for an initial Movie/Episode history event. After a successful Movie play, record the provider-scoped Movie ID with item type `movie`; after a successful Episode play, record a stable provider-scoped Episode ID with item type `episode`. The current player port provides no duration, position, progress event, or resume operation, so both initial records must retain zero duration/position and resume remains a separate design decision.

The current flat `ContentListModel` is appropriate for scalable Movie and Series catalogues. A future Series activation should show a provider-neutral detail/season/episode state rather than playing the Series. Movie and Episode playback must remain explicit activation actions only after their application resolver contracts exist. Navigation must remain runtime-capability-driven: Live-only M3U/MAG profiles expose no Movies or Series, while Xtream may expose browse-only Movies and Series until it truly implements the next contracts.

### 10.6 Async race matrix

| Scenario | Required guard | Old completion may alter catalogue, selection, loading, playing, error, or history? |
|---|---|---|
| Live A → Live B | `PlaybackAttemptRegistry` generation | **No** |
| Movie A → Movie B catalogue | PlayerShell request generation, provider ID, content type | **No** |
| Series A → Series B catalogue | PlayerShell request generation, provider ID, content type | **No** |
| Season A → Season B | Future request generation, provider ID, selected Series ID | **No** |
| Episode A → Episode B discovery | Future request generation, provider ID, Series/Season context | **No** |
| Movie A → Movie B playback | Shared playback attempt generation | **No** |
| Episode A → Episode B playback | Shared playback attempt generation | **No** |
| Episode A → Movie B playback | Shared playback attempt generation | **No** |
| Provider A → Provider B | PlayerShell request generation plus explicit pending-attempt invalidation | **No** |
| Stop → late completion | Explicit pending-attempt invalidation | **No** |

The existing native offscreen probe already confirms provider-switch invalidation, stale request protection, stale playback result protection, local non-live selection, capability navigation, and keyboard behavior. The required new discovery/load race cases remain design requirements until the corresponding application contracts are implemented.

### 10.7 Bounded Phase 8 changes

| File | Change | Reason |
|---|---|---|
| `src/samotech_iptv/presentation/viewmodels/channel_list_model.py` | Removed obsolete PySide ignores and aligned `rowCount` / `data` signatures with Qt stubs while retaining reduced fake-Qt runtime compatibility. | Fixed four strict-mypy diagnostics without changing model behavior. |
| `src/samotech_iptv/presentation/dialogs/history_library_dialog.py` | Removed obsolete PySide ignores. | Fixed two strict-mypy diagnostics. |
| `src/samotech_iptv/presentation/dialogs/favorites_library_dialog.py` | Removed obsolete PySide ignores. | Fixed two strict-mypy diagnostics. |
| `src/samotech_iptv/presentation/views/main_window.py` | Removed obsolete PySide ignores. | Fixed three strict-mypy diagnostics. |
| `tests/player_shell_performance_probe.py` | Added dynamic Movie and Series measurements for 0 through 100,000 synthetic items, including model replacement, identity, selection, category filter, search, no-match, and clear-search checks. | Extends existing scalable model evidence without provider calls. |
| `tests/test_presentation_01_player_shell_performance.py` | Asserts the new Movie/Series dynamic scale output. | Locks in non-live scale behavior. |

### 10.8 Validation, scale, typing, security, and scope evidence

| Gate | Result | Evidence |
|---|---|---|
| Focused content/provider/presentation/playback tests | **PASS** | Browse-content, playback-target, Xtream/M3U/MAG adapter, MainWindow, history dialog, and performance selections passed. |
| Full `pytest` | **PASS** | **709 tests collected**, zero failures, approximately 3 seconds using `QT_QPA_PLATFORM=offscreen`. Four existing non-fatal `aiohttp` bare-handler deprecation warnings remain. |
| Native Qt probe | **PASS (Linux offscreen only)** | All existing stale, provider-switch, content-selection, capability-navigation, and keyboard checks passed. No Windows/native GUI claim is made. |
| Dynamic scale probe | **PASS** | Live, Movie, and Series each validate `0, 1, 10, 100, 500, 1,000, 5,000, 17,431, 39,753, 100,000`; no resolver/provider-search/catalogue-reload call occurred during local operations. |
| 100,000 Movie | **PASS** | Replacement 4.474 ms; selection 0.035 ms; category filter 3.323 ms; search 27.030 ms; no-match 27.414 ms; clear search 2.143 ms. |
| 100,000 Series | **PASS** | Replacement 4.093 ms; selection 0.033 ms; category filter 3.191 ms; search 26.712 ms; no-match 25.712 ms; clear search 1.946 ms. |
| Black | **PASS** | 300 source/test files unchanged. |
| Ruff | **PASS** | No diagnostics. |
| Mypy baseline | 11 diagnostics in 4 nearby presentation files. | Recorded before implementation. |
| Mypy final | **PASS** | **Zero diagnostics** across 196 source files; all 11 safe baseline issues were corrected. |
| `git diff --check` | **PASS** | No whitespace diagnostics. |
| Security scan | **PASS** | No credentials, MAC, token, cookie, authorization header, provider payload, or resolved stream URL was added. |
| Scope audit | **PASS** | No infrastructure/provider, MAG, M3U, Xtream, VLC, `PlayerPort`, persistence, credential, transport, CI, or deployment file changed. |

### 10.9 Known limitations and exact recommendation

Movie/Series catalogue browsing is not Movie/Episode playback. The repository is **not ready for a direct bounded VOD/Episode playback implementation** because it lacks the provider-neutral resolution and discovery contracts, concrete adapter methods, sanitized translators, resolver-service hooks, application use cases, and UI hierarchy needed to do so safely. A direct Xtream-only implementation would violate the established dependency boundary and would not provide capability-honest behavior for MAG or M3U.

**Recommended next implementation increment:** first deliver a narrowly scoped **non-live provider contract increment** with no presentation playback: define the provider-neutral Movie/Episode resolver and Series-detail discovery interfaces, add stable season/episode projections, extend resolver-service capability checks, and add fake-backed contract/race tests. Implement a concrete Xtream adapter only where an authorized, sanitized fixture proves the exact endpoint and stream-resolution behavior. Only after that increment passes its own capability and security audit should explicit Movie/Episode `PlaybackTarget` dispatch and Qt detail navigation be considered.

### 10.10 Phase 8 handoff state

| Field | Value |
|---|---|
| Worktree | Intentionally uncommitted Phase 8 typing fixes, non-live scale regression coverage, and this consolidated report. |
| Commit created | **No.** |
| Push performed | **No.** |
| Protected provider/player areas | **Untouched.** |
| Implementation decision | VOD/Episode playback intentionally not implemented pending the recommended contract increment. |

---

## 11. Phase 9 — Provider-neutral non-live contract increment

### 11.1 Objective and review boundary

Phase 9 implements the **minimum provider-neutral application contract** required before any concrete Movie or Episode playback delivery can be considered. It does not add a concrete Xtream, MAG/Stalker, or M3U non-live endpoint; does not add a UI season/episode flow; does not dispatch Movie or Episode targets to the player; and does not alter `PlayerPort`, VLC, provider authentication, session management, request construction, parsing, or stream-resolution internals.

The work began from local `HEAD` `0ace7b88a38abe0dc24f3abf48c7128bdb94a0ad`, with `origin/main` at `b9e714ceb2ef31b7b0581d73fe226312d1c8fb47`. The inherited Phase 8 uncommitted typing and dynamic-catalogue regression work was preserved intact and validated together with the new Phase 9 files.

### 11.2 Provider-capability matrix

| Provider family | Movie catalogue | Series catalogue | New Movie resolver contract | New Series-detail contract | New Episode resolver contract | Phase 9 runtime claim |
|---|---:|---:|---:|---:|---:|---|
| M3U | Live-only boundary | No | No | No | No | No non-live support claimed. |
| MAG/Stalker | No verified non-live boundary | No verified non-live boundary | No | No | No | No non-live support claimed. |
| Xtream | Existing browse-only catalogue method | Existing browse-only catalogue method | No | No | No | Existing Movie/Series catalogue capability remains browse-only. |
| Phase 9 fake provider | Controlled test fixture only | Controlled test fixture only | Yes, when declared | Yes, when declared | Yes, when declared | Test-only contract proof; not a production adapter. |

> **Capability rule:** a narrow Python interface is not a support claim. `ProviderResolutionService` accepts a non-live provider only when it both satisfies the narrow interface and declares the corresponding runtime capability. Existing concrete adapters declare none of the new capabilities, so each new resolution attempt remains controlled unsupported behavior.

### 11.3 Domain, DTO, and port design

The new `Season` entity is immutable and provider-scoped through `ProviderId`, with canonical identity, parent-series linkage, positive season number, and optional non-sensitive title. The established `Episode` domain constructor remains provider-agnostic for backward compatibility. Provider scope is instead made explicit at the registered-provider discovery boundary: `LoadSeasonEpisodesRequest` contains the provider, and `EpisodeDTO` carries that provider with canonical episode, series, season, episode-number, and opaque resource identity fields. This avoids a breaking domain-constructor change while preventing a discovered episode projection from losing its provider context.

| Boundary | Added contract | Safety property |
|---|---|---|
| Domain | `Season` | Immutable provider-scoped series-season identity; no URL, credential, MAC, token, or payload fields. |
| Application DTOs | `SeasonDTO`, `EpisodeDTO`, season/episode load requests and responses | Provider-qualified, presentation-safe identity; no raw stream URL. |
| Capability vocabulary | `MOVIE_PLAYBACK`, `SERIES_DETAILS`, `EPISODE_PLAYBACK` | Separates browse capability from executable Movie, detail, and Episode capability. |
| Capability interfaces | `MoviePlaybackProvider`, `SeriesDetailProvider`, `EpisodePlaybackProvider` | Narrow asynchronous contracts for a future concrete adapter; no adapter implementation was added. |
| Additive resolver ports | `ProviderNonLivePlaybackResolverPort`, `ProviderSeriesDiscoveryResolverPort` | Preserves the existing Live/content resolver abstract interfaces and all legacy test doubles. |
| Resolver composition | New `ProviderResolutionService` methods | Enforces interface **and** declared capability; caches the same registered provider instance. |
| Playback target | `PlaybackTarget.movie()` and `.episode()` | Creates immutable provider-scoped opaque-resource identities and rejects raw `://` URLs. |

### 11.4 Discovery and race-safety behavior

`LoadSeriesSeasons` and `LoadSeasonEpisodes` are intentionally discovery-only application use cases. They use the bounded `DiscoveryAttemptRegistry`, whose monotonic generation invalidates older requests. A completed response is returned only when it remains current after the provider call and DTO projection. Provider errors become `unsupported=True`; unexpected failures become a generic non-sensitive error; stale requests become `stale=True` and expose neither an older result nor an older error.

| Scenario | Contracted result | Regression coverage |
|---|---|---|
| Same provider, Series A then Series B, B resolves first | B remains current; late A is stale. | `test_application_series_discovery.py` |
| Same Series, Season A then Season B, B resolves first | B remains current; late A is stale. | `test_application_series_discovery.py` |
| Provider switch/invalidation while discovery is pending | Pending result becomes stale. | `test_application_series_discovery.py` |
| Provider lacks a declared non-live capability | Resolver raises controlled `ProviderError`; discovery returns unsupported. | Application and resolver-service tests |
| Provider implements an interface but omits capability declaration | Resolver rejects it; no support is inferred from structure alone. | `test_infra_provider_resolution_service.py` |
| Future Movie/Episode target uses a URL-shaped resource value | Validation rejects it before dispatch. | `test_application_play_playback_target.py` |

The existing Live `PlaybackAttemptRegistry` remains the player-execution ordering mechanism. Phase 9 adds Movie/Episode target factories only; `PlayPlaybackTarget` continues to return controlled unsupported behavior for non-Live targets. Therefore no Movie or Episode URL can reach `PlayerPort.play(URL)` in this increment.

### 11.5 History and presentation position

No history schema, persistence behavior, player callback, or presentation behavior changed in Phase 9. Future Movie/Episode history must reuse the established policy: record only after a successful future provider resolution and successful `PlayerPort.play(URL)` invocation, never for a stale, unsupported, or failed attempt. Position, resume, autoplay, queue, seek, audio tracks, subtitles, and detail navigation remain outside the current scope.

The current Movie/Series catalogue remains browse-only. No new buttons, selection-triggered playback, season page, episode page, or hidden protocol call was added. The Phase 8 native player-shell and dynamic catalogue behavior remains regression-covered but is not extended into non-live playback UI.

### 11.6 Files added or changed

| Area | Phase 9 additions or changes | Purpose |
|---|---|---|
| Domain | `domain/entities/season.py`; entity exports; established `Episode` retained | Canonical Season identity without breaking Episode construction. |
| DTOs | `application/dtos/discovery.py`; package and legacy exports; target factories | Safe Season/Episode projections and future opaque non-live target identities. |
| Ports | Capability interfaces, capability enum values, `provider_non_live_resolver_port.py`, public exports | Narrow, additive Movie/Episode resolution and Series-detail discovery seams. |
| Resolver | `ProviderResolutionService` | Capability-gated, cached resolution for the three new optional capabilities. |
| Use cases | `series_discovery.py`; use-case exports | Generation-safe Season/Episode discovery only. |
| Tests | Discovery contract/race/scale, resolver capability honesty, domain Season, provider-capability vocabulary, target factory validation | Fake-backed proof without real credentials, portals, or speculative provider calls. |
| Documentation | README, architecture, application/provider guidance, project status, roadmap, gap analysis, changelog, this report | Records the contract-only status and deferred concrete work. |

### 11.7 Scale, Qt, and quality evidence

| Gate | Result | Evidence |
|---|---|---|
| Focused domain/application/resolver/adapter tests | **PASS** | Domain Episode compatibility, Season validation, target factories, Series/Season/Episode discovery races, resolver capability declaration, and Xtream adapter regression suite passed. |
| Discovery synthetic scale | **PASS** | One controlled provider response projected **1,000 Seasons** and **5,000 Episodes** with correct first/last canonical ordering; no provider-specific implementation or UI assumption was introduced. |
| Existing dynamic Movie/Series scale | **PASS** | Phase 8 probe continued to cover local model replacement/search/filter/clear through **100,000** synthetic items without provider calls. |
| Native Qt probe | **PASS — Linux offscreen only** | All existing stale identity/request/result, provider-switch, capability navigation, non-playback selection, local filtering/search, and keyboard checks passed. No Windows or real-stream claim is made. |
| Full regression | **PASS** | **728 tests collected**, zero failures, `QT_QPA_PLATFORM=offscreen`, approximately 3 seconds. Four existing non-fatal `aiohttp` bare-handler deprecation warnings remain. |
| Black | **PASS** | 305 source/test files would be left unchanged. |
| Ruff | **PASS** | No diagnostics. |
| Mypy | **PASS** | Zero diagnostics across **200** source files. |
| `git diff --check` | **PASS** | No whitespace diagnostics. |
| Protected-scope scan | **PASS** | No concrete M3U/MAG/Xtream adapter, request-builder, parser, player-port, VLC, composition, CI, or deployment file changed. |
| Sensitive-data scan | **PASS** | No credential, MAC, token, authorization header, cookie, real stream URL, or provider payload was added. Matches were documentation vocabulary and `example.invalid` fake-test URLs only. |

### 11.8 Limitations and exact next implementation step

Phase 9 is a contract and controlled-discovery increment, not non-live product delivery. Concrete providers do not implement or advertise Movie stream resolution, Series details, Episode discovery, or Episode stream resolution. There is no presentation navigation for Seasons/Episodes and no non-Live playback dispatch. Existing Live behavior remains unchanged.

**Exact next step:** use an authorized sanitized Xtream fixture to implement one concrete `SeriesDetailProvider` capability first, including canonical Season/Episode translation and explicit capability advertisement. Validate it through the existing resolver/discovery tests. Only then consider the separately approved concrete Movie or Episode resolver capability, followed by explicit application target dispatch and UI navigation in subsequent increments. Do not add MAG/Stalker or M3U non-live behavior without independent authorized evidence.

### 11.9 Delivery record

| Field | Value |
|---|---|
| Reviewed implementation commit | `ade9c1e7545bcedd56307269bc842afe64c36c41` — `feat(nonlive): add provider-neutral discovery contracts` |
| Commit scope | 33 files, 1,391 insertions, 41 deletions; includes preserved Phase 8 quality/scale work and Phase 9 contracts, tests, and documentation. |
| Push method | Normal `git push origin main`; no force push, reset, amend, or history rewrite. |
| Remote verification | `HEAD` and `origin/main` both resolved to `ade9c1e7545bcedd56307269bc842afe64c36c41`; ahead/behind was `0/0` immediately after push. |
| Post-push worktree | Clean immediately after the implementation push. A report-only follow-up commit is required to include this final delivery record in the consolidated report. |

---

## 12. MAG Catalogue Response-Boundary Diagnostic Release

### 12.1 Purpose and evidence gate

This increment makes the previously reviewed MAG response-boundary instrumentation part of the canonical source tree. It is **diagnostic-only**. It does not attempt to cure the intermittent catalogue timeout or suppress Windows `WinError 995`; both require repeated authorized runtime evidence after this release is available on `origin/main`.

The source/runtime reconciliation established that the earlier Windows process used the expected project virtual environment and imported `providers.mag.connection` from the expected project directory, but the executed source predated the uncommitted diagnostic markers. The absence of the markers therefore identified a source-revision mismatch rather than an HTTP, provider, or qasync root cause.

### 12.2 Exact diagnostic behavior

| Record | Emission boundary | Safe fields |
|---|---|---|
| `CATALOGUE_HTTP_RESPONSE` | Response headers are available, before body collection | Attempt, active total timeout, HTTP status, content type, declared content length, transfer encoding, and elapsed time. |
| `CATALOGUE_BODY_COMPLETE` | The full ordered response body is collected, before existing status/empty/JSON handling | Response byte count, chunk count, first and last body-byte timing, and body elapsed time. |
| `CATALOGUE_BODY_INCOMPLETE` | Body collection fails, or a request fails before a response exists | Available response metadata, aggregate received bytes/chunks, first-body-byte timing, last-chunk age, body elapsed time, and `TIMEOUT`, `PAYLOAD_ERROR`, or `NETWORK_ERROR`. Unavailable pre-response fields are explicit `<none>` values. |

`response.read()` is replaced by ordered `iter_chunked()` collection into one `bytearray`. Successful JSON decoding still receives the complete body in byte order. Partial bodies raise through the existing retry/error path and are never parsed or accepted. Existing malformed JSON and empty response behavior remains strict.

The release does not intentionally change timeout values, retry count or delays, profile selection, endpoints, authentication, response acceptance rules, provider configuration, playback, VLC, UI behavior, or qasync/session shutdown behavior. Its three touched runtime paths are limited to the legacy MAG transport, catalogue-stage tagging from the legacy session, and deterministic regression tests. The logs include endpoint paths but never full portal URLs, device identities, tokens, cookies, authorization headers, credentials, response bodies, or stream URLs.

### 12.3 Deterministic validation

| Gate | Result |
|---|---|
| Focused MAG provider, adapter, and integration regressions | **PASS**; includes response-boundary completion/incomplete-body, redaction, retry-count, POST-routing, session, profile, stream, and adapter coverage. |
| Full offscreen pytest regression | **PASS**; exited successfully. Four existing `aiohttp` bare-handler deprecation warnings remain non-fatal. |
| `black --check src tests providers` | **PASS**; 326 files unchanged. |
| `ruff check src tests providers` | **PASS**. |
| `mypy src` | **PASS**; no issues in 200 source files. |
| `git diff --check` | **PASS** before documentation finalization; rerun before commit. |

### 12.4 Next authorized Windows measurement

After updating from the canonical commit recorded below, use the source-installed virtual environment and launch one normal catalogue load with process-local INFO logging:

```powershell
Set-Location 'C:\samotech-iptv-player'
$py = 'C:\samotech-iptv-player\.venv\Scripts\python.exe'
$priorLogLevel = $env:IPTV_LOG_LEVEL
$env:IPTV_LOG_LEVEL = 'INFO'
try {
    & $py -m samotech_iptv
}
finally {
    $env:IPTV_LOG_LEVEL = $priorLogLevel
}
```

Collect only `CATALOGUE_HTTP_RESPONSE`, `CATALOGUE_BODY_COMPLETE`, `CATALOGUE_BODY_INCOMPLETE`, `CATALOGUE SHAPE`, `CATALOGUE PARSED`, and `MAG LOAD_CHANNELS` lines. Do not include any portal URL, provider identity, MAC address, token, cookie, authorization header, credential, response body, stream URL, or personal data. Run five consecutive loads with unchanged provider configuration before selecting a runtime classification. No timeout or lifecycle repair is justified by this release alone.

### 12.5 Delivery record

| Field | Value |
|---|---|
| Commit | `test(mag): add safe catalogue transport diagnostics`; the immutable commit ID is reported after the final amend and normal push because a Git commit cannot self-reference its own content hash. |
| Commit scope | Safe MAG transport diagnostics, deterministic tests, and directly related MAG/README/changelog/consolidated-report documentation only. |
| Push status | Completed normally for the diagnostic release at `21d12e325d74eec4102d2972f728044eb24b5851`; `HEAD` and `origin/main` matched with ahead/behind `0/0`. |

---

## 13. Independent CI Environment and SQLite Lifecycle Hardening

### 13.1 MAG runtime issue — separate evidence status

The MAG issue remains an **authorized-runtime evidence gap**, not a CI or SQLite finding. The prior committed diagnostic release observes only safe response boundaries and does not change the MAG total timeout, retry count/delay, protocol profile, request construction, response-completeness rules, session lifecycle, qasync lifecycle, or provider configuration. Five consecutive redacted Windows catalogue loads with the same authorized provider/configuration remain required to classify intermittent catalogue loading. The supplied shutdown-correlated WinError 995 remains unproven as either harmless or defective.

### 13.2 CI environment issue — proven root cause and minimal correction

The failing Ubuntu 24.04 / Python 3.13 quality job intended to execute both PlayerShell probes through pytest subprocess wrappers with `QT_QPA_PLATFORM=offscreen`. Both failed at the same PySide6 import boundary because `libEGL.so.1` was absent, before probe setup or application assertions. The wrappers contain no Windows-only branch, skip, xfail, or broad exception handling; they are valid cross-platform presentation tests.

Ubuntu package ownership verification identifies `libegl1` as the package providing `libEGL.so.1`. The quality workflow now installs that **single** package with `--no-install-recommends`, explicitly imports `PySide6.QtGui` and `PySide6.QtWidgets` under offscreen mode, and executes both standalone probes before the existing coverage pytest command. No application package dependency, probe assertion, platform skip, test selection, coverage behavior, CodeQL workflow, or Windows build workflow changed.

| CI check | Result in available Ubuntu validation environment |
|---|---|
| `libEGL.so.1` ownership | **PASS** — owned by Ubuntu package `libegl1`. |
| `QT_QPA_PLATFORM=offscreen` PySide6 imports | **PASS** — `QtGui` and `QtWidgets` imported and `QApplication` initialized. |
| Native PlayerShell probe | **PASS** — all identity, stale-result, capability, keyboard, and playback-boundary assertions executed. |
| 39,753-channel performance probe | **PASS** — 39,753 model records; zero resolver, provider-search, and catalogue-reload calls. |

The available local runner uses Python 3.12.3, while the workflow continues to target Python 3.13. The committed workflow provisions the missing Ubuntu native library before its Python 3.13 `uv` test steps; remote CI remains the final verification of that exact interpreter/runner pair.

### 13.3 SQLite resource lifecycle — proven root cause and correction

The SQLite audit found no persistent shared connection field and no repository-level connection to close on desktop shutdown. Each database operation is dispatched through `asyncio.to_thread`, opens a connection inside that worker, and must close it before returning. The defect was that Python’s `sqlite3.Connection` transaction context manager commits or rolls back but does **not** close the connection. Every operation in the five SQLite repositories therefore leaked a short-lived connection until garbage collection; one direct test schema-inspection connection used the same incorrect pattern. This is a **production and test lifecycle defect**, not an unavoidable third-party warning.

The new internal `sqlite_connection()` context manager owns every operation-scoped connection. It applies `PRAGMA foreign_keys = ON` only for XMLTV operations, commits successful work, rolls back an exception, and closes in `finally`. The repository architecture intentionally remains short-lived and operation-scoped: no `check_same_thread` override, cross-thread connection use, QThread integration, shared SQLite connection, or qasync shutdown ordering change was added.

| SQLite area | Owner and lifecycle after correction |
|---|---|
| Provider metadata, favorites, history, theme preference | Each `asyncio.to_thread` operation owns one helper-created connection; the helper commits/rolls back and closes in the same worker. |
| XMLTV bindings | Same operation ownership, plus per-connection foreign-key enablement before work. |
| Desktop composition | Constructs stateless repository facades only; it has no persistent SQLite connection to close during desktop shutdown. |
| Direct schema-inspection test | Owns and closes its local connection explicitly. |

Focused repository, composition, and helper tests passed with `PYTHONWARNINGS=error::ResourceWarning`; the requested warnings were eliminated from that affected test set. The full coverage suite reported only four pre-existing, unrelated `aiohttp` bare-handler deprecation warnings.

### 13.4 Validation and remaining evidence boundary

| Gate | Result |
|---|---|
| `uv run --no-sync ruff check src/ tests/ providers/` | **PASS**. |
| `uv run --no-sync black --check src/ tests/ providers/` | **PASS** — 328 files unchanged. |
| `uv run --no-sync mypy src/` | **PASS** — no issues in 201 source files. |
| `QT_QPA_PLATFORM=offscreen uv run --no-sync pytest -q --cov=src --cov-report=xml` | **PASS**; coverage XML generated. |
| SQLite affected tests with `ResourceWarning` as error | **PASS**. |
| `git diff --check` | **PASS** before final documentation/commit review; rerun immediately before staging. |

No MAG root-cause classification is claimed here. The remaining external dependency is the authorized Windows five-run MAG measurement set; remote GitHub Actions is the remaining exact Ubuntu 24.04/Python 3.13 confirmation after this workflow change is pushed.

### 13.5 Delivery record

| Commit | Scope |
|---|---|
| `f256932b9f51b549194a40995caf9a340974429a` — `ci: provision Qt offscreen runtime` | Installs only `libegl1` in the Ubuntu quality job and adds explicit offscreen import/direct-probe gates. |
| `7f355a37b32954ce4ba629d517e3ea409fc81eb7` — `fix(storage): close operation-scoped sqlite connections` | Adds deterministic operation-scoped SQLite ownership, migrates all repository connection sites, closes the direct test connection, and adds lifecycle regressions. |

This report, the README, project status, and changelog are committed separately as documentation for the two implementation changes. The final pushed commit identifiers and synchronized remote state are reported in the delivery message because a Git commit cannot self-reference its own immutable content hash.

---

## 14. Bounded Live-Stream EOF Recovery — Windows-Validation Handoff

### 14.1 Evidence boundary and purpose

The controlled Windows software-decoding evidence established an unexpected native termination: the player reached `PLAYING`, emitted repeated native `BUFFERING` callbacks, then emitted `END` at approximately 63.7 seconds and `STOPPED` shortly afterwards. The explicit application shutdown occurred materially later, and the terminal events retained `last_command_cause=initial_start`. This eliminates an application-shutdown explanation for that observed event and materially weakens a D3D11VA-only explanation because the same pattern occurred with hardware decoding disabled.

The exact native/libVLC, stream, transport, or environment cause remains **unconfirmed**. This increment is therefore a bounded user-experience mitigation and diagnostic continuation point, not a claim that the root cause was repaired. It does not alter MAG, M3U, Xtream, provider discovery, authentication, timeout values, retry configuration, stream resolution, libVLC construction options, network caching, hardware-decoding configuration, Qt/qasync lifecycle, `PlayerShell`, or `PlayerPort`.

### 14.2 Adapter-local recovery design

The existing six libVLC subscriptions remain in place. A callback first writes the already approved safe correlation event, snapshots only the non-sensitive media generation and adapter session token, and uses `call_soon_threadsafe` to schedule recovery interpretation on the owning asyncio loop. No callback performs media replacement, sleeps, or waits on the native libVLC callback thread.

| Design element | Implemented behavior |
|---|---|
| Internal state vocabulary | `IDLE`, `STARTING`, `PLAYING`, `BUFFERING`, `RECOVERING`, `STOPPING`, `STOPPED`, and `FAILED`; no new UI/public player-state API is exposed. |
| Unexpected terminal events | Current-session `END` is treated as `EOF`; current-session `STOPPED` is treated as `STOPPED`. Either requests one recovery sequence only. |
| Buffering watchdog | A watchdog starts only after native `BUFFERING`; `BUFFERING` alone does not restart playback. It requests recovery only when buffering outlives the configured deadline. |
| Media reconstruction | Recovery calls the existing `_set_media_and_play()` path, producing a new libVLC media object and media generation. It never reuses a failed input. |
| Generation/session safety | A scheduled callback must match the adapter’s current media generation and session token. Old callbacks queued before a channel/media replacement are ignored. |
| Concurrent signals | An active recovery task prevents an `EOF`, `STOPPED`, and buffering-timeout combination from scheduling parallel reconnect sequences. |
| Callback-thread behavior | Recovery work is asyncio-task based; `asyncio.sleep()` performs all delay handling without blocking the Qt or native callback thread. |

The configured policy is intentionally bounded: **five** attempts in a **45-second** recovery window, with exponential delays of **1, 2, 4, 8, and 8 seconds** (cap 8 seconds). Recovery counters reset only after **five seconds** of sustained native `PLAYING`; a transient recovered start therefore cannot immediately replenish the retry budget. When the attempt limit or recovery window is exceeded, the adapter enters `FAILED`, emits a safe aggregate abandonment record, and does not loop.

### 14.3 Intentional-action and live-only protection

Recovery invalidates its session and cancels active watchdog, recovery, and stability tasks before explicit stop, close/shutdown, pause, channel replacement, and recording media restart. Recording restart remains marked intentional until the replacement input emits its own native `PLAYING` event, preventing expected transition callbacks from being treated as faults. Resume starts a fresh eligible session; explicit stop and shutdown leave recovery disabled.

The application boundary remains live-only: `PlayPlaybackTarget` returns `UNSUPPORTED` for non-live targets before invoking `PlayerPort.play(URL)`. The VLC adapter does not infer VOD semantics, construct VOD URLs, or apply its live reconnect policy to a Movie/Episode target.

No recovery log includes a stream URL, hostname, portal URL, device identity, MAC address, credential, token, cookie, authorization header, or provider response. Recovery records contain only safe player/media identifiers, event/recovery reason, aggregate attempt count, and duration.

### 14.4 Deterministic regression coverage

The focused adapter suite now contains fake-backed coverage for the original playback/recording behavior, all approved correlation diagnostics, and the recovery controller.

| Regression case | Result |
|---|---|
| Unexpected `END`/EOF rebuilds Live media through the existing media path | PASS |
| Unexpected native `STOPPED` rebuilds Live media | PASS |
| Explicit stop and application shutdown do not restart playback | PASS |
| Channel switch cancels pending recovery | PASS |
| Stale EOF with an earlier generation/session is ignored | PASS |
| Buffering does not restart immediately; prolonged buffering does | PASS |
| Backoff is 1/2/4/8 seconds and remains capped | PASS |
| Concurrent buffering and EOF create one recovery sequence | PASS |
| Retry budget resets only after the stability window | PASS |
| Recovery stops at the configured retry limit | PASS |
| Pause and recording-media restart do not create recovery | PASS |
| Non-live target does not reach the VLC adapter | PASS |
| Existing immediate initial-play fallback remains intact | PASS |

### 14.5 Validation record

| Gate | Result |
|---|---|
| `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/test_infra_vlc_player_adapter.py` | **PASS** — 27 focused tests. |
| `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` | **PASS** — complete suite exited successfully. Four pre-existing non-fatal `aiohttp` bare-handler deprecation warnings remain. |
| `.venv/bin/black --check src tests` | **PASS** — 307 files unchanged. |
| `.venv/bin/ruff check src tests` | **PASS**. |
| `.venv/bin/mypy src` | **PASS** — no issues in 201 source files. |
| `git diff --check` | **PASS** before and after this report update. |

### 14.6 Remaining limitations and handoff state

The Linux/offscreen tests prove adapter ordering and bounded-task behavior through deterministic fake libVLC objects. They do **not** prove that an authorized Windows native stream will reconnect successfully after a real libVLC EOF, that the upstream stream will become available within the retry window, or that the unconfirmed native/environment cause has been removed. The appropriate next validation is a controlled Windows run with the approved safe correlation and recovery records, without changing provider configuration or VLC preferences.

| Field | Current handoff state |
|---|---|
| Production files changed | `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` |
| Focused test file changed | `tests/test_infra_vlc_player_adapter.py` |
| Documentation changed | `UI_REDESIGN_IMPLEMENTATION_REPORT.md`, `CHANGELOG.md`, `PROJECT_STATUS.md` |
| MAG/provider/VLC option/network-cache/qasync/PlayerShell changes | **None** |
| Commit created | **No** |
| Push performed | **No** |
| Root-cause claim | **No** — native libVLC/stream/transport/environment remains probable but unconfirmed. |

### 14.7 Repository reconciliation and final Windows runtime gate status

The current repository state was re-established from Git rather than from historical documentation. The actual checked-out branch is `main`; local `HEAD` and `origin/main` are both `1ecc2359eb06f4a07f7da8bd7d52f3c27014f4ab` (`docs: record CI and sqlite lifecycle findings`). The worktree contains only intentional recovery work: the adapter, its focused test module, `CHANGELOG.md`, the authoritative `PROJECT_STATUS.md`, and this consolidated report. No untracked files were present.

`PROJECT_STATUS.md` previously named an older historical baseline as the current checkout. It now identifies the actual current revision and states that the bounded Live EOF controller is **implemented but uncommitted**. Its recovery entry explicitly separates deterministic fake-backed validation, Linux/offscreen full-suite validation, and the still-required real Windows desktop validation. Historical commit references in this report and other historical records were retained unchanged.

| Repeated deterministic gate | Result |
|---|---|
| Focused offscreen adapter suite | **PASS** — 27 tests. |
| Full `QT_QPA_PLATFORM=offscreen` suite | **PASS**. Four existing non-fatal `aiohttp` bare-handler deprecation warnings were reported. |
| `black --check src tests` | **PASS** — 307 files unchanged. |
| `ruff check src tests` | **PASS**. |
| `mypy src` | **PASS** — no issues in 201 source files. |
| `git diff --check` | **PASS**. |

The requested real Windows runtime gate was **not executed**. This session runs on Linux `x86_64`, has no PowerShell executable, and has no configured Windows, desktop, computer, remote-machine, native-VLC, or authorized browser execution surface. A native Windows application run would require a 64-bit Windows desktop user session with the authorized provider environment; neither Linux/offscreen results nor fake player objects can substitute for it. No stream was opened, no provider setting was changed, and no attempt was made to synthesize or force an upstream failure.

The correct runtime classification is therefore **ENVIRONMENT LIMITATION / PENDING**: the known EOF failure was not reproduced in this session; recovery could not be observed restoring `PLAYING`; no attempt could exceed the configured budget; and no stale callback could be observed restarting an incorrect channel in a real desktop run. The deterministic tests continue to cover those lifecycle invariants. The native libVLC/stream/transport/environment root cause remains probable but unconfirmed.

---

## 15. Windows Native Validation Infrastructure

### 15.1 Scope and three validation layers

This increment builds validation infrastructure only. It does not change the bounded recovery controller, provider behavior, MAG configuration, credentials, timeout values, VLC options, network caching, hardware decoding, qasync, or `PlayerShell`. It does not automate any real provider in CI and makes no claim that an authorized IPTV EOF recovery has succeeded.

| Layer | Artifact | What it proves | What it does not prove |
|---|---|---|---|
| Native Windows libVLC lifecycle | `tests/vlc_native_lifecycle_probe.py` | Standard native libVLC can load, create/release instance/player/media, register callbacks, require first-generation `PLAYING`/`END` and replacement-generation `PLAYING`/`STOPPED`, report `BUFFERING` when emitted, and replace media. | Provider, network, or recovery behavior. |
| Deterministic recovery controller | Existing `tests/test_infra_vlc_player_adapter.py` | Bounded recovery policy, explicit-action protection, stale-session rejection, one-recovery sequencing, and redacted diagnostics. | A real native/live event sequence or upstream stream availability. |
| Authorized real Live runtime | `docs/WINDOWS_LIVE_EOF_RUNTIME_VALIDATION.md` | The actual user-visible recovery result on a configured Windows desktop. | Nothing until manually executed with an authorized source. |

### 15.2 Windows CI and native probe

The existing Windows build job now remains the smallest native infrastructure point: it uses the repository’s Python 3.13 workflow convention, installs development dependencies, installs the standard `vlc.install` Chocolatey package, runs the provider-free lifecycle probe, then runs only the focused deterministic adapter/recovery suite before the pre-existing PyInstaller step. Native VLC discovery or lifecycle failure fails the job clearly. No secret, provider, MAC identity, URL, token, cookie, authorization header, fixture payload, or IPTV request enters the job.

The probe creates a short temporary silent WAV file locally, initializes libVLC with dummy outputs, attaches callbacks that record only event labels, requires first-generation `PLAYING`/`END`, reports `BUFFERING` as `PASS` or `NOT_OBSERVED`, requires replacement-generation `PLAYING`, explicitly stops, observes replacement-generation `STOPPED`, and performs best-effort media/player/instance cleanup. It does not block inside callbacks, fetch media, contact an IPTV source, or write any path to the result. Linux execution intentionally returns `native_vlc_lifecycle=SKIP reason=windows_required`; that is a platform guard, not native lifecycle evidence.

### 15.3 Manual authorized runtime procedure

`docs/WINDOWS_LIVE_EOF_RUNTIME_VALIDATION.md` is the concise follow-on procedure. It requires a matching Windows/Python/VLC user session and an already authorized Live source, preserves all configuration, limits captured evidence to aggregate state, and classifies: recovery success, bounded exhaustion, non-reproduction, controller defect, or native VLC unavailability. It includes channel-switch and explicit-stop safety checks and explicitly prevents interpreting bounded exhaustion as a controller failure.

### 15.4 Local validation status

| Gate | Result |
|---|---|
| Linux probe syntax and platform guard | **PASS** — compiled successfully; returned `native_vlc_lifecycle=SKIP reason=windows_required`. |
| Focused recovery suite | **PASS** — 27 tests. |
| Full offscreen suite | **PASS**; four existing non-fatal `aiohttp` bare-handler deprecation warnings remain. |
| Black | **PASS** — 308 source/test files unchanged. |
| Ruff | **PASS**. |
| Mypy | **PASS** — no issues in 201 source files. |
| `git diff --check` | **PASS**. |
| Windows CI execution | **PENDING** — workflow added but not executable from this Linux session. |
| Authorized real Windows IPTV runtime | **PENDING** — no Windows desktop/authorized provider surface is available in this session. |
