# KiddaC Technology Gap Matrix

**Scope:** Evidence-backed comparison of the current SamoTech implementation with EStalker and XStreamity. This is a design and implementation decision record, not a code-cloning plan.

**Classification:** `IMPLEMENTED`, `PARTIAL`, `MISSING`, `NOT APPLICABLE`, `PROVIDER-DEPENDENT`, or `BLOCKED BY EVIDENCE`.

## Matrix

| Area | SamoTech | EStalker | XStreamity | Classification | Decision / priority | Risk |
|---|---|---|---|---|---|---|
| MAG provider | Bounded discovery, session state, live catalogue/EPG/search/link lab and adapter. Production portal remains unresolved. | Portal profiles, handshake/profile, live/VOD/Series screens, EPG, command links, Enigma2 state. | Not a MAG reference. | PARTIAL / PROVIDER-DEPENDENT | Preserve MAG infrastructure profiles and add no unsupported catalogue family. P0/P1. | High portal variance; credentials/device identity. |
| Xtream provider | Authentication, Live, categories, VOD/Series, Movie/Season/Episode, EPG, search, metadata, playback, account/server normalization. | Not an Xtream reference. | Common `player_api.php`, account/server, catalogue/detail/EPG/catch-up flows. | IMPLEMENTED / PARTIAL | Harden response variation and keep provider logic in adapter/client/translator. P0/P1. | Provider payload variation. |
| M3U | Local/file/HTTP(S) parse, canonical channels, local search, HTTP(S) playback. | Not applicable. | Not applicable. | PARTIAL | Do not redesign; maintain current provider-neutral stream boundary. | Non-HTTP transports outside current player claim. |
| Live | M3U/Xtream/MAG canonical live browsing and supported resolution, shared PlayerPort/libVLC. | Categories, paging, search/sort/filter, EPG, link resolution. | Categories, streams, EPG, local UX and player handoff. | IMPLEMENTED / PARTIAL | Reuse local search/filter/sort and existing stale-result protections. | Large catalogues and stale provider state. |
| VOD / Movies | Xtream catalogue/detail/playback through opaque IDs and `ResolvedPlayback`. | VOD rows, metadata, artwork, command-based links. | VOD categories/streams/details and container extension handling. | IMPLEMENTED / PARTIAL | Preserve existing Xtream flow; add only fixture/test hardening. | Optional fields and URL safety. |
| Series / Seasons / Episodes | Xtream Series, Season, Episode discovery and Episode resolution with generation safety. | Nested series/season/episode rows and portal commands. | `get_series_info` nested seasons/episodes and stream IDs. | IMPLEMENTED / PARTIAL | Keep canonical hierarchy and provider-scoped identity. | Empty/malformed nested arrays. |
| EPG | Xtream/MAG adapter EPG and local XMLTV boundary. | EPG/short EPG and archive markers. | Short EPG and simple data table. | PARTIAL / PROVIDER-DEPENDENT | Keep canonical EPG; do not add remote/catch-up coupling. | Timezones and provider semantics. |
| Catch-up | URL-free `CatchupEvent` model; no executable provider capability. | Provider-specific archive/time-shift behavior. | Provider-specific simple-data-table and timeshift URL. | BLOCKED BY EVIDENCE | Require provider-neutral listing and resolver contract plus authorized fixture. | Secret-bearing URL and provider-specific command risk. |
| Search | Local loaded Live/Movie/Series search and provider Live search. | Local normalized text search/filter. | Local search across loaded lists. | IMPLEMENTED / PARTIAL | Consolidate only as a shared local application utility if duplication appears. | Unicode/normalization and large lists. |
| Sort | Existing content/library ordering and provider list ordering. | Natural sort and user sort modes. | A–Z/natural sort and category-specific ordering. | PARTIAL | Add reusable canonical sort only if UI gap is confirmed; avoid screen rewrite. | User preference persistence. |
| Filter | Capability/category and local content filters exist; no full hidden/adult policy service. | Hidden/adult/parental/category filters. | Hidden categories/channels, adult settings, category filters. | PARTIAL | Add bounded local filter policy only with product requirement; keep credentials out. | Accidental content exposure/overreach. |
| Favorites | SQLite Favorites and library dialog. | Per-provider favourite state in global/file structures. | Per-provider favorite lists and watched/recents. | IMPLEMENTED | Keep SQLite canonical IDs; do not copy JSON/global state. | Provider-scoped identity collisions. |
| Hidden content | No complete persisted hidden-category service. | Hidden flags/categories and parental PIN. | Hidden categories/channels and adult settings. | PARTIAL | Defer unless required; document limitation. | Security/product policy. |
| Artwork/posters | Validated optional metadata/artwork in canonical records and card UI. | Cover/logo/backdrop async downloads and placeholders. | Cover/logo/backdrop async downloads with request IDs and cleanup. | PARTIAL | Add bounded request-owned artwork service only if current UI needs it; current UI remains safe. | Stale image overwrite and disk cache. |
| Metadata | Xtream optional metadata translation and safe account/server records. | Provider facts plus optional TMDB enrichment. | Provider facts plus optional TMDB enrichment/fallback. | PARTIAL | Keep provider facts authoritative; enrichment is optional future work. | Licensing/API keys/failure. |
| Cache | Provider runtime cache and SQLite user state foundations; bounded catalog cache is limited. | Page/cover/metadata caches and reset flows. | Playlist/page/cover caches and reset flows. | PARTIAL | Improve only with provider-scoped bounded cache and explicit invalidation tests. | Stale data/memory. |
| Provider switching | Generation/session invalidation and shared provider resolver. | Global active playlist resets. | Active playlist resets and persisted preferences. | IMPLEMENTED | Preserve generation-safe native approach; no global state. | Async race/lifecycle. |
| Playback | `ResolvedPlayback` → `PlayerPort` → libVLC; Live-only bounded EOF recovery; controls/fullscreen. | Enigma2 service/player APIs and resume. | Enigma2 service playback, resume points, infobar/aspect controls. | IMPLEMENTED / NOT APPLICABLE | Preserve player boundary and recovery policy; no Enigma2 APIs. | Backend/runtime support. |
| Recovery | Bounded Live EOF recovery only, explicitly hardened and tested. | Screen/player error callbacks and retries. | User-facing retry/refresh and player state handling. | IMPLEMENTED / PARTIAL | Do not alter recovery policy without integration evidence. | Retry loops and stale replacement. |
| Diagnostics | Redacted diagnostics and generic UI errors. | Broad print/UI diagnostics. | Generic message/retry plus some raw prints. | IMPLEMENTED | Keep safe aggregate diagnostics; reject raw secret-bearing logging. | Secret leakage. |
| UX/navigation | Modern PySide6 shell, sidebar, local search, cards, loading/empty/error states, overlay, shortcuts. | Remote-driven Enigma2 screens and keymaps. | Shared screen/key navigation across catalogue types. | IMPLEMENTED / PARTIAL | Preserve current shell; add only evidence-backed local navigation improvements. | UI thread blocking. |
| Settings/preferences | Theme, provider metadata, favorites/history, bounded settings. | Playlist/settings/global config. | Playlist and player settings, per-provider state. | PARTIAL | Keep SQLite/keyring boundaries; no filesystem credential state. | Migration/secret retention. |
| Concurrency/background work | qasync task ownership, cancellation/stale generation checks, native probes. | Timers/deferred callbacks/threaded downloads. | Download queues/timers/request IDs. | IMPLEMENTED / PARTIAL | Reuse qasync and add focused cancellation/duplicate-request tests where gaps exist. | Task leaks/races. |
| Data normalization | Canonical domain models, translators, validation, secret-free records. | Screen-row dicts/global playlist state. | Dictionaries/playlist objects/global state. | IMPLEMENTED | Do not copy reference storage shape. | Provider shape drift. |

## Architecture decision

The evidence does **not** justify creating every proposed service name in the specification. SamoTech already has provider adapters, translator boundaries, capability ports, resolver services, provider runtime cache, application task ownership, SQLite Favorites/History, canonical entities, and `PlayerPort`. The minimal decisions are:

| Proposed component | Decision | Reason |
|---|---|---|
| `ProviderSessionManager` | Do not add now. | Existing MAG session/provider lifecycle and resolver boundaries already own volatile state; a new manager would duplicate ownership. |
| `ProviderCapabilityRegistry` | Do not add now. | Existing capability declarations plus resolver capability checks are sufficient. |
| `CatalogueService` / `CategoryService` | Do not add now. | Xtream/MAG contracts differ and current application boundaries already coordinate catalogue operations. |
| `ContentSearchService` | Defer or keep local utility. | Current local search is safe and functional; introduce only when multiple screens duplicate algorithms. |
| `ContentFilterService` / `ContentSortService` | Defer. | Reference behavior is useful, but product requirements for hidden/adult/sort persistence are not fully established. |
| `FavoritesService` | Do not add now. | SQLite Favorites use cases already exist. |
| `HiddenContentService` | Defer. | No current product contract or persisted policy requirement. |
| `ArtworkService` | Defer. | Existing canonical artwork fields/card UI are safe; async artwork cache requires a concrete UI gap and disk policy. |
| `MetadataEnrichmentService` | Defer. | TMDB-style enrichment introduces external credentials/licensing and must not gate core catalogue/playback. |
| `EPGService` | Do not add now. | Existing EPG ports and XMLTV boundary are sufficient for current providers. |
| `CatchupService` | Do not add now. | Blocked until provider-neutral catch-up listing/resolution contract and authorized fixture exist. |
| `StreamResolver` | Do not add now. | Existing provider resolution service and `ResolvedPlayback` boundary already provide this role. |
| `PlaybackPreparationService` | Do not add now. | Existing application playback target factories and `PlayerPort` boundary are sufficient. |
| `ProviderCache` | Increment only if needed. | Existing runtime cache is the correct seed; add bounded catalogue/artwork caches only with measured duplication/performance evidence. |
| `RequestPolicy` | Defer. | Existing per-provider timeouts/retries and request builders cover current behavior; a common policy requires cross-provider evidence. |
| `ProviderCompatibilityLayer` | Use existing profiles only. | MAG compatibility profiles and Xtream translators already isolate provider quirks without a generic over-layer. |

## Selected implementation scope

The high-value safe work is limited to robust optional metadata/account/server normalization already within the provider boundary, realistic deterministic fixtures, explicit documentation of search/sort/filter/cache and compatibility decisions, and gap-driven tests. No Live EOF recovery rewrite, Enigma2 port, raw credential URL persistence, fabricated MAG identity, universal compatibility claim, or speculative catch-up implementation is allowed.

## References

- [EStalker source tree](https://github.com/kiddac/EStalker/tree/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker)
- [XStreamity source tree](https://github.com/kiddac/XStreamity/tree/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity)
- [External research findings](../kiddac_external_research_findings.md)


## Advanced reconciliation — 2026-08-16

The selected implementation scope has now delivered the previously deferred bounded artwork increment, but only for provider-supplied URLs. `BoundedArtworkLoader` is provider-scoped, shared-session, TTL/LRU, byte-bounded, cancellation-safe, URL-safe, and covered by deterministic tests. It is not a global page cache and does not perform external enrichment.

The Favorites row is **IMPLEMENTED / PARTIAL** after adding optional provider identity, legacy SQLite migration, same-provider duplicate prevention, provider-aware dialog display, and Movie/Series action buttons. Episode Favorites remain blocked by the current domain item-type contract. The History/resume row remains **PARTIAL / DEFERRED** because neither completion-aware provider-scoped state nor typed player position/seek APIs exist. This audit adds no fake resume or watched threshold.

The architecture decision against broad reference-service proliferation remains in force. No `ProviderSessionManager`, generic `ContentSearchService`, external `MetadataEnrichmentService`, or provider-specific catch-up/player service was added. Real populated Xtream acceptance remains blocked by unavailable authorized content evidence.
