# KiddaC Technology Adaptation

**Status:** Source study and minimal implementation decision record, 2026-08-16.

## Purpose and method

EStalker and XStreamity were studied as engineering evidence. Their Enigma2 screens, global playlist state, filesystem assumptions, service references, decoder APIs, and credential-bearing legacy behaviors were not copied. The adaptation target is SamoTech’s existing Python/domain/application/infrastructure/PySide6/libVLC architecture.

Every observation is separated into three levels. A **source-derived fact** is directly visible in a reference source or README. An **engineering inference** explains why that pattern is useful but may not be guaranteed by the source. A **proposed SamoTech design** is an application decision that must fit existing contracts and tests.

## Source-derived facts

| Reference | Observed fact | Source |
|---|---|---|
| EStalker | MAG/Stalker flows construct portal/profile requests, perform handshake/profile work, carry token/MAC/cookie/header state, retrieve live/category/EPG data, and resolve links through provider commands. | [server.py](https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/server.py), [utils.py](https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/utils.py) |
| EStalker | VOD/Series screens use page state, local search/sort/filter, hidden/favorite/watched flags, asynchronous artwork, request IDs, fallback images, and optional TMDB enrichment. | [vod.py](https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/vod.py), [series.py](https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/series.py) |
| XStreamity | Xtream workflows use a shared `player_api.php` family for account/server, category, stream, detail, EPG, and catch-up actions. | [playlists.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/playlists.py), [serverinfo.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/serverinfo.py) |
| XStreamity | VOD details merge `movie_data`/`info`; Series details return nested seasons and episodes; playback paths use provider IDs and container extensions. | [vod.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/vod.py), [series.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/series.py) |
| XStreamity | Live/VOD/Series screens expose local search, sort, filter, hidden/adult policies, favorites, watched/recents, paging, artwork fallbacks, and deferred loading. | [live.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/live.py), [vod.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/vod.py), [series.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/series.py) |
| XStreamity | Catch-up uses provider-specific simple-data-table/timeshift behavior and legacy player/service/resume APIs. | [catchup.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/catchup.py), [vodplayer.py](https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/vodplayer.py) |

## Safe SamoTech adaptations

The current SamoTech implementation already contains the highest-value safe equivalents for provider isolation, normalized translation, capability declarations, qasync task ownership, stale-result/provider-switch invalidation, canonical Movie/Series/Season/Episode identities, SQLite Favorites/History, redacted diagnostics, `ResolvedPlayback`, `PlayerPort`, shared libVLC ownership, and deterministic native Qt probes.

The new implementation increment is intentionally narrow. Movie and Series catalogue pages now offer category filtering, loaded-content search, and opt-in local sorting by provider order, title, year, or rating. Provider order remains the default to preserve existing response-order behavior. The controls operate on canonical DTO snapshots and do not issue network requests. Native probe coverage verifies the control and a large-catalogue performance probe verifies identity and local rendering behavior through 100,000 records.

## Rejected or deferred behavior

| Reference technique | Decision | Reason |
|---|---|---|
| Enigma2 UI screens, keymaps, service references, global playlist dicts | Rejected. | Incompatible with PySide6/application ports and would bypass SamoTech state ownership. |
| Raw credential-bearing Xtream/MAG/timeshift URLs in persistence or domain DTOs | Rejected. | Violates credential and playback URL boundaries. |
| Fabricated MAG250/MAG254 identity or undocumented handshake retries | Rejected. | Unsafe and not supported by authorized runtime evidence. |
| OS cache flushing and legacy filesystem state | Rejected. | Not portable and conflicts with SQLite/keyring ownership. |
| Automatic provider failover and decoder-specific recovery | Deferred. | Requires an explicit provider/player contract and evidence; Live EOF recovery must remain unchanged. |
| TMDB-style enrichment | Deferred. | External API credentials, licensing, caching, and failure behavior require a separate approved contract. |
| Hidden-content policy | Deferred. | The product lacks a complete persisted policy contract; current category/search controls are safer and sufficient. |
| Executable catch-up | Blocked. | Requires provider-neutral event listing/resolution and authorized sanitized fixtures; reference-specific timeshift construction is not a contract. |
| Audio/subtitle selection | Deferred. | `PlayerPort` does not currently expose a typed track-selection contract; UI inference would be unsafe. |

## Test strategy

Sanitized deterministic tests cover Xtream user/server/account variations, optional and malformed metadata, empty and nested VOD/Series responses, opaque playback IDs, provider capability gating, MAG handshake/session/lifecycle and response boundaries, local search, provider switching, stale async results, cache invalidation, playback target safety, credential redaction, and native Qt navigation. The new sort control is exercised by the native probe; the performance probe verifies that local content model replacement, selection, category filtering, search, and identity remain bounded through 100,000 records.

No test depends on a real IPTV provider. No real credential, provider secret, or credential-bearing provider URL is committed.

## External research and licensing

Additional research reviewed MIT `chazlarson/py-xtream-codes`, GPL-3.0 `superolmo/pyxtream`, Apache-2.0 `clubanderson/clubTivi`, and Unlicense `iptv-org/iptv`. The projects were used for corroborating design ideas and license-aware comparison only. No external source code was copied and no new dependency was added.

## References

See [KIDDAC_TECHNOLOGY_GAP_MATRIX.md](../KIDDAC_TECHNOLOGY_GAP_MATRIX.md) and the source-linked findings in `/home/ubuntu/kiddac_estalker_forensic_findings.md`, `/home/ubuntu/kiddac_xstreamity_forensic_findings.md`, and `/home/ubuntu/kiddac_external_research_findings.md`.


## Current audit increment — 2026-08-16

A follow-up product audit compared the source trace with public sanitized Xtream API documentation and typed client references. Those references corroborate the existing SamoTech choices: account/server metadata, live/VOD/Series category and detail actions, short EPG, nested seasons/episodes, opaque stream identifiers with container extensions, and defensive handling of provider response variation. One public API reference explicitly documents duplicate keys, content-dependent fields, inconsistent date/timestamp forms, numbered-object arrays, and base64 fields; this supports defensive translation rather than a rigid universal schema.

The only production change selected from this review was no new provider code. Deterministic tests now cover an expired account versus an active zero-content account and a safe unusual `webm` container extension. The adapter/client/translator already provide the appropriate boundary. Public GitHub metadata for EStalker and XStreamity exposed no SPDX license, and the inspected trees exposed no tracked root license file; README acknowledgment therefore avoids any claim of permission or code-reuse rights.
