# Package Layout

## Source Tree (Phase B.0)

```
src/samotech_iptv/
├── __init__.py
├── version.py
├── py.typed                          ← PEP 561 marker
│
├── core/
│   ├── config.py / constants.py / logging.py
│   └── exceptions.py / result.py / events.py / typing.py
│
├── domain/
│   ├── entities/                        ← one file per entity
│   │   ├── channel.py
│   │   ├── category.py / playlist.py / movie.py / series.py
│   │   ├── episode.py / stream.py / provider.py
│   │   └── epg_entry.py / favorite.py / history.py
│   ├── value_objects/                   ← one file per value object
│   │   └── provider_id.py / channel_id.py / stream_id.py / url.py / credential.py
│   ├── repositories/                    ← one file per interface
│   │   └── channel_repository.py / playlist_repository.py / ...
│   ├── events/                          ← grouped by concern
│   │   └── provider_events.py / playback_events.py / library_events.py
│   └── [entities.py / value_objects.py / repositories.py / events.py]  ← shims
│
├── application/
│   ├── ports/                           ← one file per port
│   │   ├── provider_port.py
│   │   ├── player_port.py / storage_port.py
│   │   ├── credential_store_port.py / notification_port.py
│   │   └── provider_capabilities.py        ← ISP interfaces
│   ├── dtos/                            ← one file per domain concern
│   │   └── provider.py / auth.py / channels.py / categories.py
│   │       epg.py / stream.py / history.py / favorites.py
│   ├── use_cases/                       ← one file per use-case
│   └── [ports.py / dtos.py]             ← shims
│
├── infrastructure/  (Phase B.1+)
│   └── providers/ player/ database/ network/ security/ configuration/
│
└── presentation/    (Phase D)
    └── views/ dialogs/ viewmodels/ widgets/ theme/
```

## Import Convention

```python
# Canonical (Phase B.0+)
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.application.ports.provider_capabilities import CatalogProvider
from samotech_iptv.application.dtos.channels import ChannelDTO

# Flat package (also valid)
from samotech_iptv.domain.entities import Channel
from samotech_iptv.application.ports import CatalogProvider

# Shim (Phase A compat, deprecated)
from samotech_iptv.domain.entities import Channel  # via shim
from samotech_iptv.application.ports import ProviderPort  # via shim
```
