# Application Layer

## Responsibility

The `application` package orchestrates IPTV workflows through use cases, canonical domain records, presentation-safe DTOs, and abstract ports. It translates requests from presentation or an eventual application entry point into domain operations while delegating all I/O—including providers, SQLite, keyring, networking, and libVLC—to infrastructure implementations.

## Dependency rules

```text
application → domain
application → core
application → standard library
```

The package must not import infrastructure or presentation modules, instantiate concrete repositories/adapters, or perform direct HTTP/SQLite/keyring/libVLC I/O. Presentation receives DTOs or safe response objects; provider protocol payloads, credentials, tokens, and sessions must not cross this boundary.

## Current ports and use-case groups

| Area | Current role |
|---|---|
| Provider capabilities | Fine-grained authentication, session, catalogue, category, VOD, series, EPG, search, playback-resolution, and advertised-capability contracts. |
| Provider lifecycle | Registration, cataloguing, and resolver ports permit secure provider profile registration and capability-specific construction without exposing secrets. |
| Playback | `PlayerPort` supports the application’s provider-to-player boundary. `PlayChannel` and `PlayRegisteredChannel` resolve authorized streams before invoking the sole infrastructure backend, libVLC. |
| Provider browsing | Registered-provider channel browse/search/EPG use cases return safe DTOs for Qt dialogs. |
| User library | Favorite, history, and recording use cases operate on canonical identifiers and local repositories rather than stream URLs or credentials. |
| Theme settings | Load/save use cases depend on a non-secret theme-preference repository. |

## Playback orchestration

`PlayChannel` receives a `PlaybackProvider` and `PlayerPort`, resolves an authorized canonical URL, and passes only that URL to the player. `PlayRegisteredChannel` resolves a registered provider’s playback capability and can record safe history after successful playback start. Provider credentials, MAC identities, tokens, protocol DTOs, and sessions remain inside infrastructure.

**libVLC through `python-vlc` is the sole supported player and recording backend.** The application layer does not choose or import concrete player implementations.

## Current lifecycle limitation

These use cases are implemented and tested as independently composed components. The repository does not yet provide a production composition root that initializes persistent stores, restores provider metadata, creates the provider graph/use cases, loads the persisted theme, and starts the Qt runtime. That is the current milestone; see [../../../PROJECT_STATUS.md](../../../PROJECT_STATUS.md) and [../../../ROADMAP.md](../../../ROADMAP.md).
