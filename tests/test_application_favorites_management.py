from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.use_cases.list_favorites import ListFavorites
from samotech_iptv.application.use_cases.remove_favorite import RemoveFavorite
from samotech_iptv.domain.entities.favorite import Favorite

if TYPE_CHECKING:
    from collections.abc import Sequence


class FakeFavoriteRepository:
    """In-memory favorite repository double for application use-case coverage."""

    def __init__(self, favorites: Sequence[Favorite]) -> None:
        self.favorites = list(favorites)
        self.deleted_ids: list[str] = []

    async def list_all(self) -> list[Favorite]:
        return self.favorites

    async def save(self, favorite: Favorite) -> None:
        self.favorites.append(favorite)

    async def delete(self, favorite_id: str) -> bool:
        self.deleted_ids.append(favorite_id)
        before = len(self.favorites)
        self.favorites = [favorite for favorite in self.favorites if favorite.id != favorite_id]
        return len(self.favorites) != before


@pytest.mark.asyncio
async def test_list_favorites_returns_safe_summary_dtos() -> None:
    repository = FakeFavoriteRepository(
        [
            Favorite(
                id="favorite-1",
                item_id="channel-1",
                item_type="channel",
                added_at=datetime(2026, 8, 12, tzinfo=UTC),
            )
        ]
    )

    response = await ListFavorites(repository).execute()  # type: ignore[arg-type]

    assert response.error is None
    assert [
        (favorite.id, favorite.item_id, favorite.item_type) for favorite in response.favorites
    ] == [("favorite-1", "channel-1", "channel")]


@pytest.mark.asyncio
async def test_remove_favorite_delegates_opaque_favorite_identifier() -> None:
    repository = FakeFavoriteRepository([])

    response = await RemoveFavorite(repository).execute("favorite-1")  # type: ignore[arg-type]

    assert response.removed is False
    assert response.error is None
    assert repository.deleted_ids == ["favorite-1"]


@pytest.mark.asyncio
async def test_list_favorites_returns_generic_failure_without_storage_details() -> None:
    class FailingFavoriteRepository(FakeFavoriteRepository):
        async def list_all(self) -> list[Favorite]:
            raise RuntimeError("private storage path unavailable")

    response = await ListFavorites(FailingFavoriteRepository([])).execute()  # type: ignore[arg-type]

    assert response.favorites == []
    assert response.error == "Unable to load favorites"
    assert "private" not in response.error
