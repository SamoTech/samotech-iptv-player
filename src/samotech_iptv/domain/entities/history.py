"""History entity — a single playback history record."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["History"]


@dataclass(frozen=True)
class History:
    """A single playback history record."""

    id: str
    item_id: str
    item_type: str  # "channel" | "movie" | "episode"
    watched_at: datetime
    duration_seconds: int = 0
    position_seconds: int = 0
