"""SaveFavorite use-case."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import SaveFavoriteRequest, SaveFavoriteResponse
from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.error_taxonomy import safe_user_message
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
            provider_id=request.provider_id,
        )
        try:
            await self._repo.save(favorite)
        except Exception as exc:  # noqa: BLE001
            log_exception(_log, "SaveFavorite error", exc, item_id=request.item_id)
            return SaveFavoriteResponse(
                success=False,
                error=safe_user_message(exc, fallback="Unable to save favorite"),
            )
        return SaveFavoriteResponse(success=True)
