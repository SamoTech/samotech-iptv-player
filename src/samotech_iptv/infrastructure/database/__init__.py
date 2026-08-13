"""SQLite-backed infrastructure repositories."""

from samotech_iptv.infrastructure.database.sqlite_favorite_repository import (
    SQLiteFavoriteRepository,
)
from samotech_iptv.infrastructure.database.sqlite_history_repository import (
    SQLiteHistoryRepository,
)
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.database.sqlite_xmltv_binding_repository import (
    SQLiteXMLTVBindingRepository,
)

__all__ = [
    "SQLiteFavoriteRepository",
    "SQLiteHistoryRepository",
    "SQLiteProviderMetadataRepository",
    "SQLiteXMLTVBindingRepository",
]
