"""Remove a persisted user favorite through the application boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import RemoveFavoriteResponse

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories.favorite_repository import FavoriteRepository

__all__ = ["RemoveFavorite"]


class RemoveFavorite:
    """Delete one favorite record by its opaque favorite identifier."""

    def __init__(self, repository: FavoriteRepository) -> None:
        self._repository = repository

    async def execute(self, favorite_id: str) -> RemoveFavoriteResponse:
        """Remove the requested favorite record."""
        try:
            removed = await self._repository.delete(favorite_id)
        except Exception:  # noqa: BLE001
            return RemoveFavoriteResponse(removed=False, error="Unable to remove favorite")
        return RemoveFavoriteResponse(removed=removed)
