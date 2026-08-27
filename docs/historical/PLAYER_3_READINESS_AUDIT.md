# SamoTech IPTV Player 3 Readiness Audit

**Audit date:** 2026-08-16  
**Repository:** `SamoTech/samotech-iptv-player`  
**Baseline:** `c64670c682cff43819b5022b551bd107250b9457`  
**Branch/state:** `main`, synchronized with `origin/main`, clean before this audit

> This is a read-only current-state audit. No production implementation change was made before this report. The Player 2 architecture, provider boundaries, shared libVLC player, qasync ownership, generation/session guards, stale-result protection, and bounded Live EOF recovery are preserved as non-negotiable constraints.

## Ordered dependency Todo List

| Order | Task | Dependency | Current status |
| ---: | --- | --- | --- |
| 1 | Synchronize with `origin/main` and inspect the complete repository state | None | **COMPLETE** |
| 2 | Build the protocol/capability gap matrix from concrete interfaces and adapters | 1 | **COMPLETE** |
| 3 | Harden Xtream capability-aware commercial workflows and synthetic fixture coverage | 2 | **PENDING** |
| 4 | Prepare safe authorized Xtream real-runtime procedure and classify evidence | 3 | **PENDING / runtime-dependent** |
| 5 | Audit MAG/Stalker non-live scope and implement only evidence-backed pieces | 2 | **PENDING / provider-dependent** |
| 6 | Audit EPG non-blocking behavior and add safe fields/cache policy only if supported | 2 | **PENDING** |
| 7 | Audit catch-up/archive and add a provider-neutral model only with resolver evidence | 2 | **PENDING / provider-dependent** |
| 8 | Continue commercial PlayerShell controls and status UX | 3, 5, 6, 7 | **PENDING** |
| 9 | Verify fullscreen, keyboard, overlay, and single-surface invariants | 8 | **PENDING** |
| 10 | Harden history/resume/completion/provider-content identity | 8 | **PENDING** |
| 11 | Audit provider-scoped favorites and stale-state invalidation | 3, 5 | **PENDING** |
| 12 | Improve catalogue search/filter/sort/pagination/large-data behavior | 3 | **PENDING** |
| 13 | Audit artwork cache/invalidation and playback independence | 3 | **PENDING** |
| 14 | Harden safe error taxonomy and diagnostics | 3, 5, 6, 8 | **PENDING** |
| 15 | Run the dedicated concurrency/lifecycle matrix | 3–14 | **PENDING** |
| 16 | Run measurable performance probes through 10K/50K/100K/250K where practical | 12, 13 | **PENDING** |
| 17 | Perform changed-file security review and redaction scan | All implementation tasks | **PENDING** |
| 18 | Expand unit/integration/migration/concurrency/UI/native coverage | Each implementation task | **PENDING** |
| 19 | Execute Linux and Windows-native validation with honest classification | 8, 9, 18 | **PENDING / platform-dependent** |
| 20 | Prepare controlled authorized real-provider acceptance procedures | 3–7, 19 | **PENDING / authorization-dependent** |
| 21 | Reconcile project and Player 3 documentation, including existing KiddaC attribution | 1–20 | **PENDING** |
| 22 | Run full verification, fix, and re-verify | 1–21 | **PENDING** |
| 23 | Write the 36-section `PLAYER_3_FINAL_AUDIT.md` | 22 | **PENDING** |
| 24 | Create logical commits, push normally, verify clean synchronized `origin/main` | 23 | **PENDING** |
| 25 | Deliver the single final report | 24 | **PENDING** |

## Capability Gap Matrix

| Capability | Current implementation | Evidence | Missing | Risk | Recommended action | Test required | Real-runtime required? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Xtream authentication/account/server | `XtreamProviderAdapter` and `XtreamApiClient` implement authentication, account info, and server info through the credential boundary | Adapter/client source and existing tests | Capability-aware UI detail and broader action negotiation | Unsupported server actions may be treated as generic failures | Add explicit safe capability probing/classification without assuming every action | Empty/malformed/auth-failure/HTTP-error/timeout fixtures | Yes for real acceptance; no for synthetic hardening |
| Xtream Live | Live categories, streams, local search, EPG, and stream resolution are executable | `_CAPABILITIES`, adapter/client, resolver tests | Pagination and richer server-side search | Full-catalogue reloads can be expensive | Preserve local fallback; add paging only where response evidence exists | 0/1/thousands, cancellation, provider switch | Yes for acceptance |
| Xtream VOD | Categories, full VOD load, detail, metadata, opaque playback, local presentation search/sort | Adapter, translator, content tests | Server-side search/pagination, trailer/next-episode semantics, broader capability summary | Large full snapshots and server variation | Introduce optional provider paging/search ports only if concrete response evidence supports them | Malformed/null metadata, duplicates, empty, timeout, cancellation | Yes for populated acceptance |
| Xtream Series/Episodes | Series categories/listing, detail, seasons, episodes, episode playback | Adapter, translator, concurrency and native shell tests | next/previous episode, episode artwork/season artwork propagation, server paging/search | Stale nested requests and missing IDs | Add only safe navigation metadata and guards | Missing season/episode/ID, provider switch, cancellation | Yes for populated acceptance |
| MAG/Stalker Live | Authentication/session, live categories, channels, EPG, local search, live stream resolution | `_MAG_CAPABILITIES`, adapter, MAG lab/docs/tests | VOD, series, episode, catch-up, provider-specific non-live workflows | Protocol family and portal policy are unresolved | Keep live-only; investigate from authorized evidence before adding ports | Session expiry, invalid token, retries, cleanup | Yes for any non-live claim |
| M3U/M3U8 | Playlist parse/load, live catalogue/search, supported HTTP(S) resolution | `_CAPABILITIES`, parser/adapter tests | VOD/series semantics, catch-up, EPG binding, paging | M3U metadata varies and source may be secret-bearing | Keep live-only unless a canonical metadata contract is justified | Empty/malformed/large playlists, secure-source redaction | Real source optional, not required for current scope |
| Generic HTTP/HLS/MPEG-TS | URI validation/classification; playback delegated to libVLC | stream value objects, resolved playback, VLC tests | Runtime capability negotiation and protocol-specific diagnostics | Classification is not playback support | Preserve classification-only semantics | Invalid URI/transport and resolved-playback tests | Native/media runtime required for support claim |
| VOD | Xtream Movie path only | Player 2 audit, adapter/use-case tests | Broader provider support and populated runtime evidence | Provider-specific response variance | Keep capability-gated | target/resolution/stale tests | Yes for acceptance |
| Series | Container navigation only | PlayerShell and use-case tests | No direct play by design; richer next/previous semantics | Confusing container/player state | Keep non-playable | navigation/state tests | No direct Series playback claim |
| Episodes | Xtream Episode target/player path | adapter/use-case/shell tests | next episode, previous episode, richer episode artwork/watched UX | Incorrect identity on duplicate IDs | Add only provider-scoped navigation fields | duplicate/missing ID and rapid switch tests | Yes for populated acceptance |
| Live | Shared path plus bounded EOF recovery | adapter/state/recovery tests, Player 2 docs | non-blocking EPG overlay and explicit reconnect UX | Regression of recovery or false resume | Preserve five-attempt/45-second/backoff/stale guards | recovery, switch, stop, shutdown matrix | Windows/real source for runtime acceptance |
| Catch-up/archive | `CatchupEvent` domain record and enum only | domain entity and capability enum | provider contract, listing, target resolution, UI | Invented URL formats would be unsafe | Do not implement until provider-specific evidence exists | capability absence and future resolver tests | Yes if implemented |
| EPG | Provider EPG and local XMLTV refresh; per-channel load, bounded slice | EPG ports/adapter/service/use-case | current/next/progress/description propagation, cache, refresh scheduling, stale policy | EPG failure must not block play | Add optional presentation metadata and non-blocking cache only after contract evidence | failure isolation, timezone, malformed XML, stale response | Provider/native data helpful, not necessary for contract |
| Subtitles/audio | Native libVLC DTO enumeration/selection already exists | Player 2 adapter tests; Linux native track probe blocked | Runtime Windows/native confirmation and current-media UI selection verification | Binding/runtime mismatch | Keep evidence-gated and classify Linux blocker | malformed metadata/selection tests | Native runtime required |
| Resume/history | Provider-scoped Movie/Episode position/duration/percentage/completion/upsert | domain/SQLite/playback tests | resume UX choices, history per-record deletion, duration-change policy, logout/account migration | Wrong identity can resume wrong content | Add explicit migration/content-replacement rules | duplicate IDs, duration changes, partial/restart, provider switch | Real populated runtime helpful |
| Favorites | Provider-scoped Live/Movie/Series persistence; Episode excluded by contract | entity/repository/use-case/native tests | explicit stale-state UI and justified Episode policy | Cross-provider collision or stale list | Maintain provider scope and document Episode policy | switch/delete/idempotency | No, synthetic sufficient |
| Search/categories/filter/sort | Local snapshot search/category/sort; provider live search loads full snapshot | Player 2 performance probe, browse use cases | server paging/incremental catalogue, cross-domain search consistency | O(N) reloads and memory at large providers | Measure before changing; add paging only with provider support | 10K/50K/100K/250K where practical | No for local performance |
| Artwork | Bounded provider-scoped cache, URL safety, TTL/LRU, stale guards, non-fatal errors | loader/source and native tests | broader season/episode artwork and explicit timeout diagnostics | Stale/secret URL or playback blocking | Preserve non-blocking behavior | malformed URL, timeout, provider switch, invalid image | Real CDN optional |
| Error UX | Generic safe strings in providers/use cases/shell | source/tests/security audit | stable error taxonomy and recovery/retry status | Technical errors can be too vague | Introduce internal safe error codes mapped to user copy | auth/provider/catalogue/stream/session/recovery cases | No, synthetic sufficient |
| Diagnostics | Aggregate adapter diagnostics and safe PlayerShell Info | DTO/adapter/shell | buffering/reconnect state detail, export/telemetry policy | Leakage or confusing status | Expand only with redacted structured fields | redaction and state assertions | No |
| Recordings | Shared libVLC duplicate-output `.ts` recording | Player 2 adapter/application tests | library/index/retention | orphaned files and lifecycle complexity | Defer unrelated recording expansion | existing recording suite | Native runtime for actual file playback |
| Provider switching/auth lifecycle | Generation invalidation, task cancellation, provider metadata/keyring lifecycle | shell/use-case/provider tests | explicit logout/account-change resume/favorite migration semantics | stale callbacks or cross-account data | add deterministic identity invalidation rules | switch/logout/shutdown matrix | Real provider useful |
| Packaging/CI | GitHub CI has Ubuntu quality, Windows VLC, CodeQL, release workflow | workflow files and README | release artifact acceptance and Windows execution in current sandbox | false production-readiness claim | Keep blocking native jobs; classify local results honestly | CI config validation | Windows CI required |

## Preservation boundaries

The following are explicitly out of scope for rewrite: MAG/Stalker transport and authentication architecture, Xtream request/client architecture, M3U parser/source architecture, `PlaybackTarget`, `ResolvedPlayback`, `PlayerPort`, `VlcPlayerAdapter` ownership, `PlayerShell`/MainWindow dependency injection, qasync task ownership, generation/session guards, existing security boundaries, shared libVLC instance, and five-attempt/45-second Live EOF recovery.

EStalker and XStreamity remain technology references only. No source code, credentials, branding, assets, or implementation text is to be copied.

## Audit conclusion before implementation

The current repository is coherent and synchronized. Player 3 has meaningful opportunities in capability-aware Xtream handling, EPG metadata/non-blocking behavior, error taxonomy, next-episode UX, catalogue scaling, and evidence classification. MAG non-live and catch-up are blocked by missing provider evidence and must not be fabricated. The next implementation phase begins only after this matrix and audit are complete.
