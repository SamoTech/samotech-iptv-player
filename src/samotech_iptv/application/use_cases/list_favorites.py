"""List persisted user favorites through the application boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import FavoriteDTO, ListFavoritesResponse

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.favorite_repository import FavoriteRepository

__all__ = ["ListFavorites"]


class ListFavorites:
    """Return safe favorite record summaries for presentation."""

    def __init__(self, repository: FavoriteRepository) -> None:
        self._repository = repository

    async def execute(self) -> ListFavoritesResponse:
        """Load persisted favorites without provider secrets or stream URLs."""
        favorites = await self._repository.list_all()
        return ListFavoritesResponse(
            favorites=[
                FavoriteDTO(
                    id=favorite.id,
                    item_id=favorite.item_id,
                    item_type=favorite.item_type,
                    added_at=favorite.added_at.isoformat(),
                )
                for favorite in favorites
            ]
        )
