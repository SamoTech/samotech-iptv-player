# Domain Model

## Overview

The domain model represents the core business reality of an IPTV player.
All types are pure Python — no framework dependencies, no I/O.

## Entities

| Entity | Identity field | Description |
|--------|---------------|-------------|
| `Channel` | `ChannelId` | A live-TV channel available from a provider |
| `Category` | `id: str` | A grouping of channels or VOD content |
| `Playlist` | `id: str` | Ordered collection of channels |
| `Movie` | `id: str` | A VOD movie |
| `Series` | `id: str` | A VOD series (contains Episodes) |
| `Episode` | `id: str` | A single episode within a Series |
| `Stream` | `StreamId` | A playable media URI with metadata |
| `Provider` | `ProviderId` | Metadata about a registered content provider |
| `EPGEntry` | `id: str` | A single Electronic Programme Guide entry |
| `Favorite` | `id: str` | A user-marked favourite item |
| `History` | `id: str` | A single playback history record |

## Value Objects

| Value Object | Validates |
|-------------|----------|
| `ProviderId` | Non-blank string |
| `ChannelId` | Non-blank string |
| `StreamId` | Non-blank string |
| `URL` | Must match `^https?://\S+` |
| `Credential` | Non-blank username + non-empty password; password never logged |

## Repository Interfaces

All repositories are abstract base classes (`ABC`) with `async` methods.
Concrete implementations live in `infrastructure.database`.

| Interface | Methods |
|-----------|---------|
| `ChannelRepository` | `get_by_id`, `list_by_provider`, `list_by_category`, `search`, `upsert`, `delete_by_provider` |
| `PlaylistRepository` | `get_by_id`, `list_all`, `save`, `delete` |
| `ProviderRepository` | `get_by_id`, `list_active`, `save`, `delete` |
| `EPGRepository` | `list_by_channel`, `upsert`, `purge_stale` |
| `HistoryRepository` | `list_recent`, `record`, `clear` |
| `FavoriteRepository` | `list_all`, `save`, `delete` |

## Invariants Enforced

- `Channel.name`, `Category.name`, `Playlist.name`, `Provider.name` must not be blank.
- `EPGEntry.end` must be strictly after `EPGEntry.start`.
- `Episode.season` ≥ 1, `Episode.episode_number` ≥ 1.
- `URL` must begin with `http://` or `https://`.
- `Credential.password` is never exposed in `__repr__` or `__str__`.

## Allowed Dependencies

```
domain  →  core
domain  →  stdlib
```
