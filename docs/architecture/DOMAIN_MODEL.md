# Domain Model

## Overview

The domain model represents the core business reality of an IPTV player.
All types are pure Python — no framework dependencies, no I/O.

## Package Structure (Phase B.0)

```
domain/
    entities/         ← one file per entity
    value_objects/    ← one file per value object
    repositories/     ← one file per repository interface
    events/           ← grouped by concern
```

## Entities

| Entity | Module | Identity field | Description |
|--------|--------|---------------|-------------|
| `Channel` | `entities/channel.py` | `ChannelId` | A live-TV channel |
| `Category` | `entities/category.py` | `id: str` | A content grouping |
| `Playlist` | `entities/playlist.py` | `id: str` | Ordered channel list |
| `Movie` | `entities/movie.py` | `id: str` | A VOD movie |
| `Series` | `entities/series.py` | `id: str` | A VOD series |
| `Episode` | `entities/episode.py` | `id: str` | A series episode |
| `Stream` | `entities/stream.py` | `StreamId` | A playable URI |
| `Provider` | `entities/provider.py` | `ProviderId` | A content provider |
| `EPGEntry` | `entities/epg_entry.py` | `id: str` | A programme guide entry |
| `Favorite` | `entities/favorite.py` | `id: str` | A user favourite |
| `History` | `entities/history.py` | `id: str` | A playback record |

## Value Objects

| Value Object | Module | Validates |
|-------------|--------|-----------|
| `ProviderId` | `value_objects/provider_id.py` | Non-blank string |
| `ChannelId` | `value_objects/channel_id.py` | Non-blank string |
| `StreamId` | `value_objects/stream_id.py` | Non-blank string |
| `URL` | `value_objects/url.py` | Matches `^https?://\S+` |
| `Credential` | `value_objects/credential.py` | Non-blank user + non-empty password; never logged |

## Repository Interfaces

| Interface | Module | Methods |
|-----------|--------|---------|
| `ChannelRepository` | `repositories/channel_repository.py` | `get_by_id`, `list_by_provider`, `list_by_category`, `search`, `upsert`, `delete_by_provider` |
| `PlaylistRepository` | `repositories/playlist_repository.py` | `get_by_id`, `list_all`, `save`, `delete` |
| `ProviderRepository` | `repositories/provider_repository.py` | `get_by_id`, `list_active`, `save`, `delete` |
| `EPGRepository` | `repositories/epg_repository.py` | `list_by_channel`, `upsert`, `purge_stale` |
| `HistoryRepository` | `repositories/history_repository.py` | `list_recent`, `record`, `clear` |
| `FavoriteRepository` | `repositories/favorite_repository.py` | `list_all`, `save`, `delete` |

## Allowed Dependencies

```
domain  →  core
domain  →  stdlib
```
