"""Favorite entity — a user-marked favourite item."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._library_validation import validate_favorite

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["Favorite"]


@dataclass(frozen=True)
class Favorite:
    """A channel or VOD item the user has marked as favourite."""

    id: str
    item_id: str
    item_type: str  # "channel" | "movie" | "series"
    added_at: datetime
    provider_id: str | None = None

    def __post_init__(self) -> None:
        validate_favorite(
            record_id=self.id,
            item_id=self.item_id,
            item_type=self.item_type,
            provider_id=self.provider_id,
        )
