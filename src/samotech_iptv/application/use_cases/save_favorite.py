"""SaveFavorite use-case."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import SaveFavoriteRequest, SaveFavoriteResponse
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities import Favorite

if TYPE_CHECKING:
    from samotech_iptv.domain.repositories import FavoriteRepository

_log = get_logger("use_cases.save_favorite")


class SaveFavorite:
    """Persist a channel or VOD item as a user favourite."""

    def __init__(self, repository: FavoriteRepository) -> None:
        self._repo = repository

    async def execute(self, request: SaveFavoriteRequest) -> SaveFavoriteResponse:
        _log.info("Saving favorite %s (%s)", request.item_id, request.item_type)
        favorite = Favorite(
            id=str(uuid.uuid4()),
            item_id=request.item_id,
            item_type=request.item_type,
            added_at=datetime.now(UTC),
        )
        try:
            await self._repo.save(favorite)
        except Exception as exc:  # noqa: BLE001
            _log.error("SaveFavorite error: %s", exc)
            return SaveFavoriteResponse(success=False, error=str(exc))
        return SaveFavoriteResponse(success=True)
