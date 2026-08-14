"""List persisted user favorites through the application boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import FavoriteDTO, ListFavoritesResponse
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.favorite_repository import FavoriteRepository

__all__ = ["ListFavorites"]

_LOG = get_logger(__name__)
_ERROR = "Unable to load favorites"


class ListFavorites:
    """Return safe favorite record summaries for presentation."""

    def __init__(self, repository: FavoriteRepository) -> None:
        self._repository = repository

    async def execute(self) -> ListFavoritesResponse:
        """Load persisted favorites without provider secrets or stream URLs."""
        try:
            favorites = await self._repository.list_all()
        except Exception:  # noqa: BLE001
            _LOG.error("Unable to load favorites")
            return ListFavoritesResponse(error=_ERROR)
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
