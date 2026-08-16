# KiddaC Compatibility Matrix

**Authority:** Current SamoTech behavior is defined by `PROJECT_STATUS.md`; this document records the specific EStalker/XStreamity comparison and evidence limits.

| Surface | SamoTech current state | EStalker evidence | XStreamity evidence | Readiness | Limitation / next evidence |
|---|---|---|---|---|---|
| Provider registration and credentials | M3U, Xtream, and MAG profiles use safe metadata/keyring boundaries. | Playlist/global config stores provider state and credentials in legacy files. | Playlist config stores Xtream credentials and account/server state. | IMPLEMENTED | SamoTech intentionally does not persist raw credentials in metadata or UI state. |
| MAG portal normalization | Bounded candidate discovery and compatibility profiles exist in infrastructure. | Multiple portal/profile assumptions and endpoint families are visible. | Not applicable. | PARTIAL / PROVIDER-DEPENDENT | Production portal compatibility requires a valid authorized handshake. |
| MAG handshake/session | MAG adapter/session state, cleanup, expiry, and local middleware lab exist. | Handshake/profile/token/MAC-cookie ordering is source-derived. | Not applicable. | PARTIAL / BLOCKED BY EVIDENCE | Supplied authorized portal returned no token-bearing machine-readable handshake. |
| MAG live catalogue | Canonical live channels, local search, EPG, and link resolution exist. | Category/list pagination and command link paths exist. | Not applicable. | PARTIAL | Authorized production fixture still needed. |
| MAG VOD/Series | Not advertised. | Reference has VOD/Series screens but provider contract varies. | Not applicable. | BLOCKED BY EVIDENCE | No verified SamoTech MAG VOD/Series contract or fixture. |
| Xtream account/server | Normalized `AccountInfo`/`ServerInfo`, API extraction, translator, adapter, and resolver ports exist. | Not applicable. | `user_info`/`server_info` are base API concepts. | IMPLEMENTED | Real runtime content evidence remains separate. |
| Xtream Live | Categories, streams, search, EPG, and supported playback exist. | Not applicable. | Common category/stream/EPG actions exist. | IMPLEMENTED | Provider payload variations remain possible. |
| Xtream VOD/Movies | Categories, details, optional metadata, local category/search/sort, Movie playback, and shared PlayerPort handoff exist. | Not applicable. | VOD category/list/detail and extension-based URLs exist. | IMPLEMENTED / PARTIAL | Populated authorized real-provider playback remains pending. |
| Xtream Series/Seasons/Episodes | Series → Season → Episode navigation and Episode playback exist with generation safety. | Not applicable. | Nested `get_series_info` seasons/episodes exist. | IMPLEMENTED / PARTIAL | Populated authorized real-provider validation remains pending. |
| Search | Local loaded-content search and provider live search. | Local search/filter. | Local search over content families. | IMPLEMENTED | Server-side search is not needed for loaded snapshots. |
| Sort | Local opt-in provider order/title/year/rating sort. | Natural/category sort. | A–Z and category sort. | IMPLEMENTED | More user preferences are optional future work. |
| Filter | Category selector and local query filtering. | Hidden/adult/parental filters. | Hidden/adult/category filters. | PARTIAL | Full hidden/adult policy requires a product contract. |
| Favorites | SQLite Favorites and presentation library. | Per-provider favourite flags/files. | Per-provider favorites/recents. | IMPLEMENTED | SamoTech uses safer canonical IDs and SQLite. |
| Hidden categories/content | No complete persisted hidden-content service. | Present in legacy plugin state. | Present in playlist/screen settings. | PARTIAL | Deferred until policy/storage requirements are explicit. |
| Artwork/posters | Canonical optional artwork and card presentation. | Async cover/logo/backdrop fallback/cache. | Async cover/logo/backdrop fallback/cache. | PARTIAL | Dedicated bounded artwork cache is future work if measured necessary. |
| Metadata/TMDB | Provider metadata translation and safe optional fields. | Provider + optional TMDB enrichment. | Provider + optional TMDB enrichment. | PARTIAL | External service/license/credential contract not approved. |
| EPG | Xtream/MAG EPG and local XMLTV. | EPG and archive markers. | Short EPG and simple-data-table. | PARTIAL | Remote XMLTV caching and catch-up remain open. |
| Catch-up/timeshift | URL-free `CatchupEvent`; no executable capability. | Provider-specific archive commands. | Provider-specific timeshift URL. | BLOCKED BY EVIDENCE | Must define safe provider-neutral resolver and fixture first. |
| Cache | Provider runtime cache and SQLite user state; bounded content cache limited. | Page/artwork/metadata caches and reset. | Playlist/page/artwork caches and reset. | PARTIAL | Add only measured, bounded, provider-scoped caches. |
| Provider switching | Generation/session invalidation and stale-result protection. | Global active-playlist reset. | Active-playlist reset. | IMPLEMENTED | Native SamoTech approach avoids global state. |
| Playback handoff | Provider → `ResolvedPlayback` → `PlayerPort` → libVLC. | Enigma2 service/player APIs. | Enigma2 service/player/resume APIs. | IMPLEMENTED | Enigma2 player behavior is intentionally not portable. |
| EOF/recovery | Existing Live-only bounded EOF recovery. | Legacy player callbacks/retry behavior. | Legacy player controls/resume. | IMPLEMENTED / PRESERVED | No recovery policy change without integration evidence. |
| Diagnostics | Redacted structured diagnostics and generic UI errors. | Broad legacy print/UI diagnostics. | Generic error/retry plus raw prints. | IMPLEMENTED | Secrets, tokens, MACs, and raw URLs remain excluded. |
| Performance/concurrency | qasync ownership, cancellation, stale generations, native probes; 100,000-record performance coverage. | Timers/deferred downloads/global callbacks. | Download queues/timers/request IDs. | IMPLEMENTED / PARTIAL | More provider-side pacing requires measured evidence. |
| External source licensing | No source code copied; no added dependency. | Reference repository license applies to reference code. | Reference repository license applies to reference code. | IMPLEMENTED | External research licenses recorded in adaptation documentation. |

## Classification definitions

`IMPLEMENTED` means executable through the stated SamoTech boundary and covered by tests. `PARTIAL` means a real subset exists but a user-facing workflow, provider contract, or runtime evidence is incomplete. `PROVIDER-DEPENDENT` means behavior varies by portal/provider and cannot be generalized. `BLOCKED BY EVIDENCE` means implementation would require inventing an undocumented contract or using unavailable authorized runtime evidence. `REJECTED` means a reference behavior conflicts with security, portability, licensing, or architecture constraints.

## References

- [EStalker source](https://github.com/kiddac/EStalker/tree/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker)
- [XStreamity source](https://github.com/kiddac/XStreamity/tree/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity)
- [KIDDAC technology adaptation](KIDDAC_TECHNOLOGY_ADAPTATION.md)
- [KIDDAC technology gap matrix](../KIDDAC_TECHNOLOGY_GAP_MATRIX.md)

## SamoTech status reconciliation — 2026-08-16

The Movie/Series detail row is **PARTIAL by deliberate boundary**: SamoTech now exposes provider-supplied optional metadata and an inline detail panel with deterministic fallback, while remote artwork loading/cache and external metadata enrichment remain deferred. The local search, sort, category/filter, provider switching, playback handoff, and diagnostics rows remain as classified above. No EStalker or XStreamity source code was copied, and their behavior is treated only as technical reference.


## Advanced reconciliation — 2026-08-16

The earlier Artwork/posters row is updated from “future work” to **IMPLEMENTED / PARTIAL** for provider-supplied artwork only. SamoTech now uses a shared-session, provider-scoped, bounded TTL/LRU loader with URL safety, response-size limits, native Qt decode/error placeholders, stale-generation protection, and provider invalidation. External TMDB-style enrichment remains **DEFERRED / REJECTED** until a product, licensing, credential, and privacy contract exists.

The Favorites row is **IMPLEMENTED / PARTIAL**: Favorites carry optional provider identity, legacy SQLite rows migrate safely, same-provider duplicates are prevented, and Movie/Series actions are exposed. Episode Favorites remain outside the existing domain item-type contract. The History/resume behavior is **PARTIAL / DEFERRED** because the existing History and `PlayerPort` contracts do not provide provider-scoped completion or typed seek/progress capabilities.

The safe adaptation boundary remains unchanged: EStalker and XStreamity were inspected only as engineering references. No Enigma2 service APIs, global playlist state, decoder controls, provider-specific legacy URL construction, credential persistence, or source code were copied. Live EOF recovery, MAG, M3U, shared libVLC ownership, qasync task ownership, and stale-result protections remain preserved.
