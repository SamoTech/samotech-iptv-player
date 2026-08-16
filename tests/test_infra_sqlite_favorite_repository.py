from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from samotech_iptv.domain.entities.favorite import Favorite
from samotech_iptv.infrastructure.database.sqlite_favorite_repository import (
    SQLiteFavoriteRepository,
)


@pytest.mark.asyncio
async def test_sqlite_favorite_repository_saves_lists_and_deletes_favorites(tmp_path: Path) -> None:
    repository = SQLiteFavoriteRepository(tmp_path / "favorites.sqlite3")
    favorite = Favorite(
        id="favorite-1",
        item_id="channel-1",
        item_type="channel",
        added_at=datetime(2026, 8, 12, tzinfo=UTC),
        provider_id="provider-a",
    )

    await repository.initialise()
    await repository.save(favorite)

    assert await repository.list_all() == [favorite]
    assert await repository.delete("favorite-1") is True
    assert await repository.delete("favorite-1") is False
    assert await repository.list_all() == []


@pytest.mark.asyncio
async def test_sqlite_favorite_repository_prevents_duplicate_provider_scoped_items(
    tmp_path: Path,
) -> None:
    repository = SQLiteFavoriteRepository(tmp_path / "favorites.sqlite3")
    first = Favorite(
        id="favorite-1",
        item_id="movie-1",
        item_type="movie",
        added_at=datetime(2026, 8, 12, tzinfo=UTC),
        provider_id="provider-a",
    )
    duplicate = Favorite(
        id="favorite-2",
        item_id="movie-1",
        item_type="movie",
        added_at=datetime(2026, 8, 13, tzinfo=UTC),
        provider_id="provider-a",
    )
    other_provider = Favorite(
        id="favorite-3",
        item_id="movie-1",
        item_type="movie",
        added_at=datetime(2026, 8, 14, tzinfo=UTC),
        provider_id="provider-b",
    )

    await repository.initialise()
    await repository.save(first)
    await repository.save(duplicate)
    await repository.save(other_provider)

    assert [item.id for item in await repository.list_all()] == ["favorite-3", "favorite-1"]


@pytest.mark.asyncio
async def test_sqlite_favorite_repository_migrates_legacy_schema(tmp_path: Path) -> None:
    database = tmp_path / "legacy.sqlite3"
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE favorites (id TEXT PRIMARY KEY, item_id TEXT NOT NULL, "
            "item_type TEXT NOT NULL, added_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO favorites VALUES (?, ?, ?, ?)",
            ("legacy-1", "series-1", "series", "2026-08-12T00:00:00+00:00"),
        )
        connection.commit()

    repository = SQLiteFavoriteRepository(database)
    await repository.initialise()

    favorites = await repository.list_all()
    assert favorites[0].id == "legacy-1"
    assert favorites[0].provider_id is None
