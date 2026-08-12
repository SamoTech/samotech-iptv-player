# Domain Layer

## Responsibility

The `domain` package models provider-independent IPTV business records and validation. It contains canonical channels, categories, playlists, streams, providers, EPG entries, movies, series, episodes, favorites, history, stable IDs, credentials, validated URLs, stream transports/manifests, provider capabilities, and theme preference. It does not represent raw provider payloads, HTTP responses, Qt widgets, player objects, database rows, or session state.

## Dependency rules

```text
domain → core
domain → standard library
```

The domain must not import infrastructure, application, presentation, Qt, libVLC, SQLite, `aiohttp`, keyring, or provider-specific libraries. It performs no network, filesystem, database, keyring, or player I/O.

## Current package structure

| Package | Current contents |
|---|---|
| `entities/` | Canonical `Channel`, `Category`, `Playlist`, `Stream`, `Provider`, `EPGEntry`, `Movie`, `Series`, `Episode`, `Favorite`, and `History` records. |
| `value_objects/` | Stable IDs, safe `URL`, credential value object, provider capabilities, stream URI/transports/manifests, and non-secret theme preference. |
| `repositories/` | Domain repository interfaces for favorites and history. |
| `services/` | Provider-independent stream classification. |

Provider adapters translate external records into these types before the application layer sees them. A provider capability or a stream transport classification is descriptive; it does not by itself promise end-to-end player support. Verified support status is maintained in [../../../PROJECT_STATUS.md](../../../PROJECT_STATUS.md).

## Security boundary

Credentials, MAC/device identities, session tokens, tokenized source URLs, and resolved playback URLs must not be added to domain records unless a value object explicitly models safe validation/redaction behavior. Long-lived storage and volatile session ownership belong outside the domain. See [../../../ARCHITECTURE.md](../../../ARCHITECTURE.md) and [../../../SECURITY.md](../../../SECURITY.md).
