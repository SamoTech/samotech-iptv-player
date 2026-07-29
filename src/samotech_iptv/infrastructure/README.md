# Infrastructure Layer

## Responsibility

The `infrastructure` package contains all concrete I/O adapters.  It is the
only layer permitted to import third-party libraries such as `aiohttp`,
`aiosqlite`, or `keyring`.

## Sub-packages

| Package | Responsibility |
|---------|---------------|
| `providers/` | Adapter implementations of `ProviderPort` (MAG, Xtream, M3U) |
| `player/` | Adapter implementations of `PlayerPort` (MPV, WinRT) |
| `database/` | Repository implementations (`aiosqlite`) |
| `network/` | HTTP client factory, retry middleware |
| `security/` | `CredentialStorePort` implementation (OS keyring) |
| `configuration/` | File-based and env-based config loaders |

## Migration Note

The legacy `providers/` package at the repository root is **not** moved yet.
Phase B will introduce the `ProviderPort` adapters here and route the
registry through `application.ports.ProviderPort`.

## Allowed Dependencies

```
infrastructure  →  application (ports, DTOs)
infrastructure  →  domain
infrastructure  →  core
infrastructure  →  aiohttp, aiosqlite, keyring, ...
```

## Forbidden

- `presentation`
