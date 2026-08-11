"""History entity — a single playback history record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._library_validation import validate_history

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

    def __post_init__(self) -> None:
        validate_history(
            record_id=self.id,
            item_id=self.item_id,
            item_type=self.item_type,
            duration_seconds=self.duration_seconds,
            position_seconds=self.position_seconds,
        )
