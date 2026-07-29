# Domain Layer

## Responsibility

The `domain` package is the heart of the application.  It models the
business reality of an IPTV player: channels, categories, playlists,
streams, EPG entries, providers, favourites, and history.

## Rules

- **Immutable entities** — all entities use `@dataclass(frozen=True)` or
  `@dataclass(eq=True)` with explicit `__hash__`.
- **No I/O** — no network calls, no file reads, no database access.
- **No framework dependencies** — stdlib + `samotech_iptv.core` only.
- **Repository interfaces** are abstract base classes (`ABC`) defined here;
  concrete implementations live in `infrastructure`.

## Modules

| Module | Contents |
|--------|----------|
| `entities.py` | `Channel`, `Category`, `Playlist`, `Movie`, `Series`, `Episode`, `Stream`, `Provider`, `EPGEntry`, `Favorite`, `History` |
| `value_objects.py` | `ProviderId`, `ChannelId`, `StreamId`, `Credential`, `URL` |
| `repositories.py` | Abstract repository interfaces |
| `events.py` | Domain-specific event types |

## Allowed Dependencies

```
domain  →  core
domain  →  stdlib
```

## Forbidden

- `infrastructure`, `application`, `presentation`
- `aiohttp`, `SQLite`, `keyring`, any third-party library

## Future Guidance

- Validation belongs in entity `__post_init__` using `core.exceptions.ValidationError`.
- Domain events (`core.events.DomainEvent` subclasses) should be raised by
  entity factory methods, not by setters.
- Repository interfaces must be `async` to allow both in-memory and async
  database implementations.
