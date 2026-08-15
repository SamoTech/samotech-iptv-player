from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

from samotech_iptv.infrastructure.database.sqlite_connection import sqlite_connection
from samotech_iptv.infrastructure.database.sqlite_favorite_repository import (
    SQLiteFavoriteRepository,
)
from samotech_iptv.infrastructure.database.sqlite_history_repository import SQLiteHistoryRepository
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.database.sqlite_theme_preference_repository import (
    SQLiteThemePreferenceRepository,
)
from samotech_iptv.infrastructure.database.sqlite_xmltv_binding_repository import (
    SQLiteXMLTVBindingRepository,
)


class _TrackingConnection(sqlite3.Connection):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.was_closed = False

    def close(self) -> None:
        self.was_closed = True
        super().close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repository",
    [
        SQLiteFavoriteRepository,
        SQLiteHistoryRepository,
        SQLiteProviderMetadataRepository,
        SQLiteThemePreferenceRepository,
        SQLiteXMLTVBindingRepository,
    ],
)
async def test_sqlite_operation_connections_close_after_each_operation(
    tmp_path: Path,
    repository: Callable[[Path], object],
) -> None:
    original_connect = sqlite3.connect
    opened: list[_TrackingConnection] = []

    def track_connect(*args: object, **kwargs: object) -> _TrackingConnection:
        connection = original_connect(*args, factory=_TrackingConnection, **kwargs)
        opened.append(connection)
        return connection

    with patch(
        "samotech_iptv.infrastructure.database.sqlite_connection.sqlite3.connect",
        side_effect=track_connect,
    ):
        await repository(tmp_path / "state.sqlite3").initialise()  # type: ignore[attr-defined]

    assert opened
    assert all(connection.was_closed for connection in opened)


def test_sqlite_connection_rolls_back_and_closes_after_operation_error(tmp_path: Path) -> None:
    database_path = tmp_path / "state.sqlite3"
    with closing(sqlite3.connect(database_path)) as setup_connection:
        setup_connection.execute("CREATE TABLE records (value TEXT NOT NULL)")
        setup_connection.commit()

    captured: sqlite3.Connection | None = None
    with pytest.raises(RuntimeError, match="synthetic failure"):
        with sqlite_connection(database_path) as connection:
            captured = connection
            connection.execute("INSERT INTO records (value) VALUES ('uncommitted')")
            raise RuntimeError("synthetic failure")

    assert captured is not None
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        captured.execute("SELECT 1")
    with closing(sqlite3.connect(database_path)) as verification_connection:
        assert verification_connection.execute("SELECT COUNT(*) FROM records").fetchone() == (0,)
