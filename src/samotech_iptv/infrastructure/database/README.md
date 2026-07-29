# Infrastructure / Database

## Phase A Status

Empty scaffold.

## Phase B Plan

- `SqliteChannelRepository(ChannelRepository)`
- `SqlitePlaylistRepository(PlaylistRepository)`
- `SqliteEPGRepository(EPGRepository)`
- `SqliteHistoryRepository(HistoryRepository)`
- `SqliteFavoriteRepository(FavoriteRepository)`

All backed by `aiosqlite` with a single database file in `AppConfig.data_dir`.
