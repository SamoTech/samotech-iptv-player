# Package Layout

## Source Tree

```
src/samotech_iptv/
├── __init__.py               # package root, version export
├── version.py                # single source of truth for version string
│
├── core/                     # infrastructure-independent primitives
│   ├── __init__.py
│   ├── README.md
│   ├── config.py             # AppConfig, NetworkConfig, PlayerConfig
│   ├── constants.py          # named constants
│   ├── logging.py            # get_logger(), configure_logging()
│   ├── exceptions.py         # SamotechError hierarchy
│   ├── result.py             # Result[T, E] / Ok / Err
│   ├── events.py             # DomainEvent base
│   └── typing.py             # shared type aliases / protocols
│
├── domain/                   # pure business model
│   ├── __init__.py
│   ├── README.md
│   ├── entities.py           # Channel, Category, Playlist, Movie, ...
│   ├── value_objects.py      # ProviderId, ChannelId, StreamId, URL, Credential
│   ├── repositories.py       # abstract repository interfaces
│   └── events.py             # domain event types
│
├── application/              # use-case orchestration
│   ├── __init__.py
│   ├── README.md
│   ├── ports.py              # ProviderPort, PlayerPort, StoragePort, ...
│   ├── dtos.py               # request/response DTOs
│   └── use_cases/
│       ├── __init__.py
│       ├── authenticate_provider.py
│       ├── load_channels.py
│       ├── load_categories.py
│       ├── load_epg.py
│       ├── resolve_stream.py
│       ├── search_channels.py
│       ├── save_favorite.py
│       ├── load_history.py
│       └── refresh_provider.py
│
├── infrastructure/           # I/O adapters (Phase B+)
│   ├── __init__.py
│   ├── README.md
│   ├── providers/            # ProviderPort implementations
│   ├── player/               # PlayerPort implementations
│   ├── database/             # repository implementations
│   ├── network/              # HTTP client factory
│   ├── security/             # CredentialStorePort implementation
│   └── configuration/        # config file loaders
│
└── presentation/             # MVVM UI (Phase D)
    ├── __init__.py
    ├── README.md
    ├── views/
    ├── dialogs/
    ├── viewmodels/
    ├── widgets/
    └── theme/
```

## Legacy Packages (migration window)

```
providers/          # ← untouched until Phase B migration
tests/              # ← existing MAG provider tests, unchanged
```

## Import Convention

```python
# New code — canonical
from samotech_iptv.domain.entities import Channel
from samotech_iptv.application.ports import ProviderPort
from samotech_iptv.core.exceptions import SamotechError

# Legacy — still valid during migration window
from providers.mag_provider import MAGProvider
```
