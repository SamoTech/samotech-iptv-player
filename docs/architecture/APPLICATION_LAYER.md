# Application Layer

## Overview

The application layer orchestrates use-cases.  It translates requests
from the presentation layer into domain operations and delegates all I/O
to infrastructure through port interfaces.

## Ports

| Port | Responsibility |
|------|---------------|
| `ProviderPort` | Content provider adapter (authenticate, load channels, resolve stream, load EPG) |
| `PlayerPort` | Media player backend (play, stop, pause, resume) |
| `StoragePort` | Persistence adapter initialisation / teardown |
| `CredentialStorePort` | Secure credential storage (store, retrieve, delete) |
| `NotificationPort` | User-facing notifications (info, warning, error) |

## Use Cases

| Use Case | Input | Output |
|----------|-------|--------|
| `AuthenticateProvider` | `AuthenticateRequest` | `AuthenticateResponse` |
| `LoadChannels` | `LoadChannelsRequest` | `LoadChannelsResponse` |
| `LoadCategories` | `LoadCategoriesRequest` | `LoadCategoriesResponse` |
| `LoadEPG` | `LoadEPGRequest` | `LoadEPGResponse` |
| `ResolveStream` | `ResolveStreamRequest` | `ResolveStreamResponse` |
| `SearchChannels` | `SearchChannelsRequest` | `SearchChannelsResponse` |
| `SaveFavorite` | `SaveFavoriteRequest` | `SaveFavoriteResponse` |
| `LoadHistory` | `LoadHistoryRequest` | `LoadHistoryResponse` |
| `RefreshProvider` | `RefreshProviderRequest` | `RefreshProviderResponse` |

## DTOs

DTOs are frozen dataclasses.  Domain entities are **never** returned
directly to the presentation layer; they are always mapped to DTOs.

## Dependency Rules

```
application  →  domain
application  →  core
application  →  stdlib
```

**Forbidden:** `infrastructure`, `presentation`, any third-party library.
