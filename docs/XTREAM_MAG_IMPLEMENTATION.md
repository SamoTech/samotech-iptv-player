# Xtream and MAG Implementation Record

**Status:** Verified against the current repository after the 2026-08-16 implementation increment.

## Scope and evidence

This record compares SamoTech’s current provider boundaries with the observed behavior of EStalker and XStreamity. The reference projects were used as protocol evidence, not as architecture templates. EStalker’s readable source shows MAG/Stalker handshake, profile/account, live catalogue, EPG, and command-based link flows. XStreamity’s source shows Xtream `player_api.php` account/server responses, live/VOD/Series catalogue actions, detail calls, short EPG, and legacy catch-up/timeshift behavior. The source observations are recorded in the audit notes and are cited in the final report.

## Current normalized model set

| Model | Purpose | Secret policy | Executable provider support |
|---|---|---|---|
| `Provider` | Registered non-secret provider metadata and declared capabilities. | No credentials, tokens, cookies, or raw failure text. | Existing provider registry and resolution service. |
| `ProviderSession` | Volatile normalized lifecycle state. | No token, cookie, MAC, password, or URL. | MAG’s existing session state remains infrastructure-owned; the model is safe for future application status use. |
| `AccountInfo` | Optional account status, expiry, and connection limits. | No username/password or credential-bearing URL. | Xtream via `AccountInfoProvider` and `ProviderResolutionService`. |
| `ServerInfo` | Optional non-secret server name, version, timezone, and protocol. | Server URL is deliberately excluded. | Xtream via `ServerInfoProvider` and `ProviderResolutionService`. |
| `Channel`, `Movie`, `Series`, `Season`, `Episode`, `EPGEntry` | Canonical content and guide records. | Only validated metadata and opaque provider-scoped IDs. | Existing Xtream, MAG, M3U, and XMLTV boundaries as declared. |
| `CatchupEvent` | Normalized archived-programme identity and time interval. | No resolved private playback URL. | Domain model only; no provider currently advertises executable catch-up. |

## Capability matrix

| Capability | Xtream | MAG/Stalker | Decision |
|---|---:|---:|---|
| Authentication | Implemented and tested. | Implemented and tested through the existing MAG facade and lab. | Preserve existing provider-specific authentication boundaries. |
| Session | Credential-safe client reuse and explicit MAG session state exist. | Implemented with refresh, expiry, and cleanup. | Do not expose tokens or cookies. |
| Account information | Implemented through normalized `user_info`. | Not advertised; current facade does not provide a verified account-information contract. | Do not claim unsupported MAG account support. |
| Server information | Implemented through normalized `server_info`. | Not advertised; no verified current contract. | Do not claim unsupported MAG server support. |
| Live, categories, EPG, search, stream resolution | Implemented and tested. | Implemented and tested for the supported live/session subset. | Preserve current ports and adapter boundaries. |
| VOD, Series, Movie, Episode playback | Implemented for Xtream. | Not advertised. | MAG requires a separate verified contract and fixture before implementation. |
| Catch-up/timeshift | Normalized event model exists, but no executable provider capability. | Not advertised. | Reference-specific timeshift URL construction is excluded until a safe provider-neutral contract is proven. |

## Security and boundary decisions

Credential-bearing Xtream URLs remain infrastructure-local. The API client and request builder may construct them only for remote requests or provider resolution; the domain, application DTOs, presentation layer, logs, reports, fixtures, and persisted metadata do not retain them. Server URL fields returned by provider payloads are ignored by `ServerInfo`. Invalid optional status, expiry, connection-count, artwork, and metadata values degrade to safe unknown/absent values where the existing translator contract permits it. Required content identities and time bounds continue to fail closed through `ValidationError`.

The existing `PlayerPort` and libVLC integration were not modified. Providers still resolve streams through `ResolvedPlayback`, and the presentation layer does not infer provider URLs or player capabilities. Reference behaviors involving Enigma2 global state, OS cache flushing, raw credential-bearing URL persistence, fabricated MAG device identities, or unverified random-token/prehash sequences remain excluded.

## Verification evidence

The final gate run passed the complete offscreen pytest suite with coverage, the deterministic native Qt/player probe, Ruff, Black, mypy over `src`, and `git diff --check`. Focused tests cover the new domain records, Xtream API response extraction, active/expired/unknown status normalization, sparse and malformed metadata, adapter methods, resolver capability gating, and secret-free model boundaries. Existing MAG protocol/session/lifecycle, Xtream VOD/Series, concurrency, stale-result, provider-switch, search, cache, and playback-boundary tests remain green.

## Open compatibility limits

The reference repositories do not prove compatibility with a production provider. The supplied/authorized real MAG portal remains unresolved because no token-bearing machine-readable handshake was obtained in the bounded investigation. Populated real Xtream VOD/Series playback remains pending authorized runtime evidence. MAG VOD, Series, and executable catch-up remain blocked until authorized, sanitized response fixtures establish their exact contracts. These limitations are intentional readiness classifications, not hidden workarounds.
