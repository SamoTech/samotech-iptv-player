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

Current provider adapters are capability-oriented. A provider implements only the applicable contracts such as `CatalogProvider`, `PlaybackProvider`, `EPGProvider`, `SearchProvider`, `VodProvider`, `SeriesProvider`, `CategoryProvider`, `AuthenticationProvider`, or `SessionProvider`. The adapter’s actual advertised capabilities are the support claim—not a generic interface, an enum value, or a future design note.

## Stream resolution and playback

The application’s `PlayChannel` use case resolves an authorized canonical URL through `PlaybackProvider` and passes it to `PlayerPort`. `PlayRegisteredChannel` first resolves the selected provider from the provider resolver, then delegates the same provider-to-player boundary. The Qt presentation layer attaches the native video surface before requesting playback but does not resolve provider streams or access credentials.

**libVLC through `python-vlc` is the sole supported player and recording backend.** The current adapter supports play, pause, resume, stop, active-state checks, native output attachment, and duplicate-output local `.ts` recording. The architecture does not currently support MPV, WinRT, FFmpeg, or another desktop media backend.

## Desktop composition status

`desktop_bootstrap.build_desktop_application()` creates or reuses `QApplication`, applies a supplied initial theme, builds the libVLC adapter, and creates `MainWindow` from externally supplied use cases. `desktop_runtime.run_desktop_application()` runs that composed window through `qasync`.

Those are tested composition boundaries, not a finished application lifecycle. The repository currently has no production composition root or executable entry point that initializes repositories, restores metadata, constructs provider services/use cases, loads the persisted theme, runs the UI, and closes resources. Completing that lifecycle is the current roadmap milestone.

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

## Current architectural gaps

The primary current gap is lifecycle composition, not another provider protocol abstraction. The next implementation increment should assemble the existing registry/factory/context, secure stores, SQLite repositories, theme preference, use cases, bootstrap, and qasync runtime into a testable production composition root. Other gaps—including M3U stream resolution, VOD/series workflows, XMLTV source binding, playback controls, and production hardening—are tracked in [PRODUCT_GAP_ANALYSIS.md](PRODUCT_GAP_ANALYSIS.md).
