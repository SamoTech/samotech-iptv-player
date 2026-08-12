# Infrastructure Layer

## Responsibility

The `infrastructure` package owns concrete I/O and integration code. It implements application ports and translates external provider/persistence/player behavior into canonical domain records and safe application boundaries. It may import third-party libraries such as `aiohttp`, `keyring`, `defusedxml`, `python-vlc`, and PySide-independent platform facilities; it must not import presentation code.

## Current sub-packages

| Package | Current responsibility |
|---|---|
| `providers/` | Capability-oriented M3U, Xtream Codes, and MAG/Stalker adapters; provider registration, metadata, registry/factory/context, and provider resolution. |
| `parsing/` | Extended-M3U source/parser, bounded HLS/DASH manifest parsers, and bounded secure XMLTV parser. |
| `player/` | `VlcPlayerAdapter` and composition helper. **libVLC through `python-vlc` is the sole supported player and recording backend.** |
| `database/` | SQLite repositories for non-secret provider metadata, favorites, history, and theme preference. |
| `security/` | OS-keyring-backed provider credential store. |
| `network/` | Shared async HTTP client and network errors used by provider/source adapters. |
| `configuration/` | Environment-backed configuration provider. |
| `plugins/` | Trusted local provider-plugin loader implementation. |

The repository-root `providers/` package remains a legacy MAG protocol implementation used behind `MagProviderAdapter`. It is not a second presentation or application boundary.

## Data and dependency boundaries

```text
infrastructure → application ports/DTOs
infrastructure → domain
infrastructure → core
infrastructure → approved third-party I/O libraries
```

Infrastructure must not expose raw provider payloads, credentials, MAC identities, session tokens, secure M3U source URLs, or resolved playback URLs to application or presentation code. It must translate provider records into canonical domain entities/value objects and use generic safe errors across user-facing boundaries.

Provider metadata in SQLite is non-secret. Credentials and sensitive source strings belong in the OS keyring. Provider sessions/tokens are volatile runtime state. See [../../ARCHITECTURE.md](../../ARCHITECTURE.md), [../../PROJECT_STATUS.md](../../PROJECT_STATUS.md), and [../../SECURITY.md](../../SECURITY.md).

## Lifecycle status

The package contains the required building blocks for a production desktop composition root, but no production root currently initializes repositories, restores metadata, constructs the provider graph, loads the persisted theme, starts the UI, and closes resources. That gap is the current milestone in [../../ROADMAP.md](../../ROADMAP.md).
