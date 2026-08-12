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
    )

    await repository.initialise()
    await repository.save(favorite)

    assert await repository.list_all() == [favorite]
    assert await repository.delete("favorite-1") is True
    assert await repository.delete("favorite-1") is False
    assert await repository.list_all() == []
