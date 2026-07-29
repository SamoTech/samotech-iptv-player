# Application Layer

## Overview

The application layer orchestrates use-cases.  It translates requests
from the presentation layer into domain operations and delegates all I/O
to infrastructure through port interfaces.

## Ports (Phase B.0 — ISP Applied)

### Coarse-Grained (Backward Compatible)

| Port | Module | Responsibility |
|------|--------|---------------|
| `ProviderPort` | `ports/provider_port.py` | Full provider surface (MAG-era compatibility) |
| `PlayerPort` | `ports/player_port.py` | Media player backend |
| `StoragePort` | `ports/storage_port.py` | Persistence initialisation/teardown |
| `CredentialStorePort` | `ports/credential_store_port.py` | Secure credential storage |
| `NotificationPort` | `ports/notification_port.py` | User-facing notifications |

### Fine-Grained Capability Interfaces (ISP)

| Interface | Module | One Responsibility |
|-----------|--------|-------------------|
| `AuthenticationProvider` | `ports/provider_capabilities.py` | `authenticate`, `is_authenticated`, `provider_id` |
| `SessionProvider` | `ports/provider_capabilities.py` | `refresh_session` |
| `CatalogProvider` | `ports/provider_capabilities.py` | `load_channels` |
| `EPGProvider` | `ports/provider_capabilities.py` | `load_epg` |
| `SearchProvider` | `ports/provider_capabilities.py` | `search_channels` |
| `PlaybackProvider` | `ports/provider_capabilities.py` | `resolve_stream` |
| `CapabilityProvider` | `ports/provider_capabilities.py` | `supported_capabilities` |

## Use Cases

| Use Case | Port Dependency | DTO In | DTO Out |
|----------|----------------|--------|----------|
| `AuthenticateProvider` | `ProviderPort` + `CredentialStorePort` | `AuthenticateRequest` | `AuthenticateResponse` |
| `LoadChannels` | `ProviderPort` | `LoadChannelsRequest` | `LoadChannelsResponse` |
| `LoadCategories` | *(Phase B.1)* | `LoadCategoriesRequest` | `LoadCategoriesResponse` |
| `LoadEPG` | `ProviderPort` | `LoadEPGRequest` | `LoadEPGResponse` |
| `ResolveStream` | `ProviderPort` | `ResolveStreamRequest` | `ResolveStreamResponse` |
| `SearchChannels` | `ChannelRepository` | `SearchChannelsRequest` | `SearchChannelsResponse` |
| `SaveFavorite` | `FavoriteRepository` | `SaveFavoriteRequest` | `SaveFavoriteResponse` |
| `LoadHistory` | `HistoryRepository` | `LoadHistoryRequest` | `LoadHistoryResponse` |
| `RefreshProvider` | `ProviderPort` | `RefreshProviderRequest` | `RefreshProviderResponse` |

## Phase B.1 Migration Plan

Use-cases will be migrated to minimum required capability:

```python
# LoadChannels: ProviderPort → CatalogProvider
# LoadEPG:      ProviderPort → EPGProvider
# ResolveStream: ProviderPort → PlaybackProvider
# AuthenticateProvider: ProviderPort → AuthenticationProvider + CredentialStorePort
```

## Allowed Dependencies

```
application  →  domain
application  →  core
application  →  stdlib
```

**Forbidden:** `infrastructure`, `presentation`, any third-party library.
