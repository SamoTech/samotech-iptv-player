"""Favorite entity — a user-marked favourite item."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
