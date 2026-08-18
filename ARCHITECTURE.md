# Architecture

> **Current-state authority:** [PROJECT_STATUS.md](PROJECT_STATUS.md) defines implemented, partial, and planned support. This document defines the architectural boundaries that make provider-agnostic IPTV support possible.

## Architectural purpose

SamoTech IPTV Player uses Clean Architecture to keep provider-specific IPTV protocols, content/manifest formats, stream transports, media playback, persistence, and desktop presentation from becoming coupled to one another. The architecture lets a provider adapter translate its own remote payloads into canonical records while application use cases and Qt UI interact only with stable domain concepts and ports.

```text
Authorized IPTV provider or source
        ↓
Infrastructure provider adapter and protocol DTOs
        ↓
Infrastructure translator
        ↓
Canonical domain entities and value objects
        ↓
Application use cases and abstract ports
        ↓
Authorized stream resolution
        ↓
PlayerPort → libVLC
        ↓
PySide6/Qt desktop UI
```

## Dependency rule

Dependencies point inward. Infrastructure implements application ports; presentation invokes application use cases. The domain remains independent from Qt, libVLC, SQLite, `aiohttp`, keyring, and provider protocol libraries.

```text
Presentation → Application → Domain
                    ↑
         Infrastructure adapters implement application ports

Core is importable by all layers but imports no higher layer.
Plugins extend the provider factory through the narrow trusted-local SDK.
```

| Layer | Package | Current responsibility |
|---|---|---|
| Core | `samotech_iptv.core` | Shared exceptions, logging, configuration primitives, and other dependency-free utilities. |
| Domain | `samotech_iptv.domain` | Canonical IPTV entities, value objects, validation, repository interfaces, and stream classification. |
| Application | `samotech_iptv.application` | Use cases, presentation-safe DTOs, and abstract provider/player/storage/credential/theme ports. |
| Infrastructure | `samotech_iptv.infrastructure` | Provider adapters, parsing, SQLite repositories, keyring credential store, networking, libVLC adapter, plugin loader. |
| Presentation | `samotech_iptv.presentation` | PySide6 dialogs, views, native video surface, and application-wide theme styling. |
| Plugin SDK | `samotech_iptv.plugins` | Plugin API contracts used by explicitly selected trusted local provider plugins. |

## Terminology that must remain separate

| Concept | Definition | Examples | Architectural owner |
|---|---|---|---|
| Provider/content source | A service or source model that supplies a catalogue, authentication, EPG, or stream links. | M3U source, Xtream Codes API, MAG/Stalker; planned Ministra. | Provider adapter in infrastructure. |
| Playlist/manifest format | A document that lists content or describes media renditions. | Extended M3U, M3U8/HLS, MPEG-DASH MPD, XMLTV. | Parsers and domain stream metadata. |
| Stream transport | A URI delivery scheme. | HTTP(S), RTMP(S), RTSP, UDP, RTP, SRT. | `StreamURI` and stream classification. |
| Player backend | The engine that decodes/renders a resolved media stream. | libVLC through `python-vlc`. | `PlayerPort` implementation in infrastructure. |

A provider is not a manifest format, a manifest is not a transport, and a transport classification is not a player support promise. For example, an M3U source can contain HLS URLs, an Xtream endpoint can return a transport-stream URL, and libVLC may ultimately handle a protocol that is only classified—not negotiated—by the application.

## Provider boundary

A provider adapter owns provider-specific interpretation. It may retrieve credentials through `CredentialStorePort`, maintain private volatile session state, call remote endpoints through infrastructure networking, and translate protocol records. It must return canonical domain entities/value objects or raise safe application errors; it must not expose raw provider payloads, credentials, tokens, or session objects to the application or presentation layer.

Current provider adapters are capability-oriented. A provider implements only the applicable contracts such as `CatalogProvider`, `PlaybackProvider`, `EPGProvider`, `SearchProvider`, `VodProvider`, `SeriesProvider`, `MoviePlaybackProvider`, `SeriesDetailProvider`, `EpisodePlaybackProvider`, `CategoryProvider`, `AuthenticationProvider`, or `SessionProvider`. The adapter’s actual advertised capabilities are the support claim—not a generic interface, an enum value, or a future design note. Xtream is the current concrete non-live implementation: it advertises VOD, Series detail, Movie playback, and Episode playback against deterministic sanitized fixtures. Its translator preserves required identity, defaults missing extensions, translates available Series year/rating metadata, and ignores malformed optional Movie/Series year, rating, and artwork values without dropping otherwise valid catalogue records. M3U and MAG/Stalker do not advertise those non-live contracts.

## Stream resolution and playback

The application’s `PlayChannel` use case resolves an authorized canonical URL through `PlaybackProvider` and passes it to `PlayerPort`. `PlayRegisteredChannel` first resolves the selected provider from the provider resolver, then delegates the same provider-to-player boundary. Xtream’s `MoviePlaybackProvider`, `EpisodePlaybackProvider`, and `SeriesDetailProvider` use the same provider-neutral seam: the adapter resolves provider-specific resources, the application coordinates generation-safe playback, and `PlayerPort` consumes only `ResolvedPlayback`. The Qt presentation layer does not construct Xtream URLs or access credentials. Non-live UI handlers also carry a provider/content/action generation and reject stale, switched-provider, navigated-away, or disposed-owner completions before state or playback mutation.

**libVLC through `python-vlc` is the sole supported player and recording backend.** The current adapter supports play, pause, resume, stop, active-state checks, native output attachment, and duplicate-output local `.ts` recording. The architecture does not currently support MPV, WinRT, FFmpeg, or another desktop media backend. The detailed current-state source/protocol/media-plane mapping is maintained in [docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md).

## Current protocol and media-plane boundary

M3U, Xtream Codes, and MAG/Stalker are provider/source control-plane integrations, not VLC protocols. They resolve catalogue records and, where the current contract permits, produce an HTTP(S) `ResolvedPlayback` target. libVLC then owns network input, buffering, demuxing, decoding, and rendering. The domain can classify additional URI schemes, but the current executable `URL` boundary accepts only HTTP(S); classification is not a playback-support promise. Enigma2 service/player values such as `1`, `4097`, `5001`, `5002`, and `8193` belong to KiddaC’s Enigma2 backend selection and must not be copied into SamoTech’s libVLC layer. See [docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md](docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md).

## Desktop composition status

`desktop_bootstrap.build_desktop_application()` creates or reuses `QApplication`, applies a supplied initial theme, and creates `MainWindow` from externally supplied use cases and an optional shared player. It creates the libVLC adapter itself only when a caller does not inject one. `desktop_runtime.run_desktop_application()` runs that composed window through `qasync`.

`desktop_composition.build_production_desktop_application()` is the production dependency-wiring root. It builds the provider context/registry/factory, initializes non-secret SQLite repositories, restores provider metadata, constructs registration/catalogue/resolution services and presentation use cases, loads the persisted theme, builds one libVLC player, and injects that same player into registered playback, recording, and the Qt video surface. It neither starts the qasync loop nor closes runtime resources.

The executable lifecycle is now delivered through the `samotech-iptv` console command and `python -m samotech_iptv`. The entry point invokes production composition, runs the qasync UI loop, emits only a generic startup failure message, and closes the shared HTTP resource after the event loop exits. Packaging, installer, update, and broader diagnostic concerns remain separate production-hardening work.

## Persistence and security boundaries

| Data type | Boundary | Rules |
|---|---|---|
| Provider credentials | `CredentialStorePort` / OS keyring | Never store in SQLite metadata, logs, status text, or DTOs. |
| MAG MAC identity | Credential boundary | Treat as a sensitive device identifier; keep it out of provider metadata and UI summaries. |
| Session tokens/cookies | Live provider adapter | Volatile runtime state only; never persist or expose outside infrastructure. |
| Tokenized M3U source | Credential boundary | Store full sensitive source securely; preserve only sanitized non-secret metadata. |
| Provider metadata | SQLite metadata repository | Provider ID/type/base URL/activation/capability/source-security data only; no credentials, tokens, or error text. |
| Favorites/history/theme | SQLite repositories | Store canonical IDs/time/validated non-secret preference; never store stream URLs or provider secrets. |
| Playback URLs | Provider resolution → player | May contain sensitive access material; do not log, persist, or display unnecessarily. |

## Trusted local plugin boundary

Plugin API version 1 is for **trusted, explicitly selected local Python files** only. The loader validates plugin identity, API version, and provider-type namespace, and commits factory registrations transactionally. It does not sandbox plugin code, sign packages, scan directories, install from remote sources, run a marketplace, or perform updates. See [docs/PLUGIN_SDK.md](docs/PLUGIN_SDK.md).

## Desktop presentation architecture

The PySide6 presentation layer now uses a token-driven dark/blue design system in `presentation/theme/tokens.py`, with `theme_engine.py` applying the shared stylesheet for both light and dark preferences without changing domain or infrastructure contracts. `PlayerShell` owns presentation-only navigation state: a collapsible sidebar with persisted width/visibility, provider/status context, local search over already-loaded Live/Movie/Series models, card delegates for Movie and Series catalogues, and explicit empty/loading/error states. These surfaces consume existing application use cases and canonical DTOs; they do not construct provider URLs, access credentials, issue additional search requests, or alter playback resolution.

The shell keeps a single shared player and exposes player-only interaction through the existing `PlayerPort` path. The player overlay provides idle hide/show behavior, status text, play/pause and stop actions, fullscreen toggling, and supported keyboard shortcuts (`Space` and `F`). Overlay visibility and styling are presentation state; playback ownership, stream resolution, and provider lifecycle remain outside the UI. `MainWindow` aligns menus and the status bar with the same theme tokens while preserving the existing qasync/bootstrap/composition boundaries.

## Current architectural gaps

M3U now resolves current parsed HTTP(S) streams through `PlaybackProvider`, advertises `STREAM_RESOLUTION`, and reaches libVLC through the registered-provider path. Pause, resume, and stop are delivered as application use cases delegating only through the existing libVLC-backed `PlayerPort`; the Qt menu displays only generic success/failure feedback and does not inspect player internals. Because `PlayerPort` provides `is_playing` rather than a complete paused/stopped state model, detailed playback state remains an explicitly documented future capability rather than a presentation-layer inference. Registered-provider lifecycle management is delivered through a secure application boundary: type-aware Qt editors never prefill secrets, blank optional credential fields preserve existing OS-keyring values, and removal deletes persisted non-secret metadata, the associated credential, and any XMLTV binding before deregistering the runtime record. Registered Xtream live-category discovery is delivered through the same composition graph: the resolver verifies `CategoryProvider`, the adapter translates external responses into canonical `Category` records, and the browse-only UI renders names without content selection, stream resolution, or player access. Local XMLTV binding is now similarly explicit: a separate SQLite repository persists only a local path or local `file:` URI plus source-channel mappings; a local-only loader and bounded parser produce transient canonical EPG entries for manual Qt refresh. Remote/tokenized XMLTV sources, guide-entry caching, scheduling, and playback remain outside this boundary. The primary current gap is user-library presentation for existing favorites/history foundations. Other gaps are tracked in [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md).


## Xtream and MAG normalized provider boundaries

The provider layer now exposes normalized, secret-free `ProviderSession`, `AccountInfo`, `ServerInfo`, and `CatchupEvent` domain records. Xtream account and server metadata are retrieved through `AccountInfoProvider` and `ServerInfoProvider`, resolved through `ProviderResolutionService`, and translated without retaining credentials, tokens, or credential-bearing server URLs. MAG continues to advertise only the capabilities implemented by its existing legacy facade: authentication, session, live catalogue, EPG, local search, and stream resolution.

Xtream retains the existing Live, VOD, Series, detail, episode, EPG, search, and playback boundaries. The shared `PlayerPort`/libVLC boundary remains unchanged. Catch-up is modeled as a domain record but is not advertised as executable provider support until a safe provider-neutral listing and resolution contract is established; reference-specific `timeshift` URL construction is intentionally not copied into the application or player layers.


The non-live catalogue controls also expose an opt-in local sort selector for provider order, title, year, and rating. Sorting is performed over the already-loaded canonical DTO snapshot after category/search filtering; the default preserves provider response order. It issues no network request, changes no provider contract, and leaves Series season/episode navigation and PlayerPort handoff unchanged.


## Product-hardening adaptation — 2026-08-16

The current implementation was audited against public EStalker and XStreamity engineering patterns without importing their Enigma2 UI, global playlist state, service references, decoder APIs, credential persistence, or provider-specific legacy behavior. The safe adaptation retained SamoTech’s existing capability-gated provider resolver, canonical domain records, qasync task ownership, generation-safe non-live flows, SQLite/keyring split, `ResolvedPlayback` handoff, PySide6 shell, and libVLC-only `PlayerPort`.

The only new code increment in this audit is deterministic synthetic Xtream coverage for expired versus active zero-content accounts and a safe unusual `webm` container-extension fixture. The production adapter remains unchanged by the public-reference research because the existing translator and request boundary already cover the evidence-backed variation without a justified new abstraction. Movie/Series local search, category filtering, and opt-in title/year/rating sorting remain local operations over loaded DTO snapshots; the default preserves provider response order.

Public EStalker and XStreamity repositories are acknowledged in `README.md` as technical references. Their GitHub metadata exposed no SPDX license and the inspected trees exposed no tracked root license file; SamoTech makes no permission, endorsement, partnership, or code-reuse claim. No source code was copied and no new dependency was added. See `docs/KIDDAC_TECHNOLOGY_ADAPTATION.md`, `docs/KIDDAC_COMPATIBILITY_MATRIX.md`, and `KIDDAC_TECHNOLOGY_GAP_MATRIX.md` for the evidence record and rejected/deferred behaviors.

The existing bounded Live EOF recovery controller, provider/session contracts, and player ownership were not changed. Authorized real-provider validation, Windows desktop runtime validation, MAG production compatibility, executable catch-up, replay/resume, audio/subtitle selection, and remote XMLTV caching remain explicitly outside the current claim boundary.

## Commercial Xtream VOD/Series increment — 2026-08-16

This increment extends the existing canonical path rather than introducing a parallel architecture. Xtream provider payloads are translated by `XtreamDomainTranslator` into optional Movie and Series metadata fields, the application use cases copy those fields into `ContentItemDTO`, and `PlayerShell` renders them in the existing selection/detail surface. Required identity remains validated at the domain boundary; malformed optional provider values are discarded safely so one bad metadata field cannot remove an otherwise valid catalogue record.

The detail surface is deliberately inline and local. It presents title/episode identity, year, rating, genre, duration, format, Series season/episode counts, people, plot, and artwork availability without performing network artwork loading. Search, category filtering, and opt-in sorting continue to operate over the explicitly loaded snapshot. Playback remains unchanged: only eligible Movie/Episode targets proceed through existing `PlaybackTarget`, `ResolvedPlayback`, `PlayerPort`, and shared libVLC composition; Series records remain containers.

The change preserves qasync task ownership, generation-based stale-result protection, provider-scoped canonical identity, SQLite Favorites/History boundaries, keyring credential storage, shared libVLC lifecycle, Live-only EOF recovery, and the existing M3U/MAG/Live paths. It does not add a global image cache, resume reconstruction, catch-up, track APIs, or provider-specific URL construction in the UI.


## Advanced Xtream VOD/Series increment — 2026-08-16

The advanced non-live increment remains inside the existing dependency direction. Xtream translators continue to map provider payloads into canonical `Movie`, `Series`, `Season`, and `Episode` records; application use cases continue to expose presentation-safe DTOs; and `PlayerShell` continues to use `ResolvedPlayback` and `PlayerPort` rather than reaching into libVLC.

Artwork is now an optional application port implemented by `BoundedArtworkLoader`. Production composition injects it with the already-owned `AsyncHttpClient`, so no uncontrolled session, global image cache, provider-specific UI client, or external metadata service is introduced. Requests are keyed by `(provider_id, content_id, role, url)`, validate HTTP(S) URLs without credentials or secret-bearing query keys, enforce a per-response byte limit, use a TTL/LRU cache with both entry and byte bounds, return `None` on ordinary failures, preserve cancellation, and clear provider-scoped entries on provider changes. `PlayerShell` associates every preview with a monotonically increasing artwork generation and selected DTO identity, preventing stale A→B→A completions from mutating the current surface.

Favorites now carry an optional provider identity through the domain entity, application request/DTO, SQLite schema, and PlayerShell actions. SQLite performs a compatibility migration by adding a nullable `provider_id` to legacy tables. A save is idempotent for the same provider/item/type and still allows identical item IDs on different providers. Legacy rows remain readable and are displayed as `legacy provider`. Episode Favorites are intentionally disabled because the existing Favorite item-type contract excludes episodes.

The increment does not add watched-state inference, resume reconstruction, catch-up, audio/subtitle track APIs, external metadata enrichment, or provider-side search. The current typed player and history contracts do not provide sufficient evidence for those behaviors. Live EOF recovery, MAG, M3U, and existing VLC recovery semantics are unchanged.


## Real Xtream acceptance and production-hardening audit — 2026-08-16

The protocol review confirms the existing action and translation boundaries for live/VOD/Series categories, streams, Movie details, Series details, short EPG, opaque IDs, extensions, and provider-supplied metadata. The request builder and adapter continue to own credential-bearing URL construction; application and presentation layers receive only canonical records and `ResolvedPlayback`.

No populated authorized provider was available for this phase. The prior authorized session returned zero VOD and Series records, so real content, artwork, Movie/Episode playback, timeout, HTTP-error, and populated shutdown acceptance remain blocked or not executed. The Windows-only native lifecycle probe explicitly skips on Linux. The 10K/50K/100K performance and 50-test concurrency matrices passed without a production architecture change.

The History/PlayerPort audit confirms that resume, watched, seek, completion, and track selection cannot be safely inferred or implemented in presentation. Live EOF recovery, MAG, M3U, shared libVLC ownership, qasync task ownership, and stale-result protection remain unchanged.

## Player 2 commercial playback architecture — 2026-08-16

Player 2 extends the existing `PlaybackTarget` → `ResolvedPlayback` → `PlayerPort` → libVLC path rather than replacing provider or media architecture. `PlayerPort` now exposes evidence-backed position, duration, seek, volume, mute, native audio/subtitle tracks, restart, and aspect-ratio operations. `VlcPlayerAdapter` serializes mutations through its existing async lock and translates native events through an application-owned explicit state machine.

`PlayerShell` receives the shared application `PlayerPort` and optional history recorder through dependency injection. It never imports libVLC, constructs provider URLs, accesses credentials, or resolves provider streams. Live, Movie, and Episode modes are separated at the presentation boundary; Live does not expose seek or resume. Provider switching and playback attempts retain generation guards, and the established Live EOF recovery policy remains unchanged.

History storage now adds provider-scoped identity, nullable lifecycle timestamps, runtime progress, watched percentage, completion, and a backward-compatible SQLite migration. Resume is restored only for matching incomplete Movie/Episode history and only after successful play. Full design and runtime evidence are recorded in [`docs/PLAYER_2_ARCHITECTURE.md`](docs/PLAYER_2_ARCHITECTURE.md) and [`docs/PLAYER_2_RUNTIME_VALIDATION.md`](docs/PLAYER_2_RUNTIME_VALIDATION.md).


## Player 3 commercial hardening architecture — 2026-08-16

Player 3 extends the existing dependency direction without introducing a parallel provider or player architecture. The Xtream adapter and translator remain the only owners of Xtream payload interpretation, malformed-record policy, duplicate identity handling, and provider-specific request semantics. Invalid individual catalogue records are rejected locally; valid records continue through canonical domain entities and application DTOs. The MAG adapter remains live-oriented and now advertises `ProviderCapability.CATEGORIES` because its existing live category path is implemented and tested.

The application boundary now preserves EPG `description` and `category` metadata in `EPGEntryDTO` and clamps the presentation-facing list to a bounded maximum. `PlayerShell` owns adjacent-episode selection and backend-state labels as presentation behavior. It delegates episode selection to the existing provider-scoped catalogue snapshot and schedules playback through the established use-case path; it does not resolve URLs, inspect libVLC, access secrets, or manufacture playback state. The backend label mapping consumes the typed public state exposed by the application/player port, including buffering and recovery states.

History timestamp validation is enforced at the domain entity boundary. Safe user-facing error copy is centralized in `core.error_taxonomy` and is applied by registration, authentication, and stream-resolution use cases. These changes preserve the existing SQLite/keyring split, provider-scoped identity, qasync task ownership, generation guards, shared `PlayerPort`, libVLC-only playback, and bounded Live EOF recovery.

Catch-up/archive remains intentionally outside the executable architecture: no current provider advertises `ProviderCapability.CATCHUP`, so no URL construction, fake archive model, or UI promise was added. MAG VOD/Series/Episodes remain outside the claim boundary until an authorized portal trace establishes a compatible contract. Windows native validation and populated authorized Xtream acceptance remain environment/provider acceptance gates rather than architectural assumptions.

## Player 3 boundary references

The implementation and evidence are recorded in [PLAYER_3_FINAL_AUDIT.md](../PLAYER_3_FINAL_AUDIT.md), [docs/PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md](PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md), the focused provider/application/presentation tests, and [docs/PLAYER_3_RUNTIME_VALIDATION.md](PLAYER_3_RUNTIME_VALIDATION.md). Public reference-study attribution remains in [README.md](../README.md) and does not change the source-ownership boundary.
