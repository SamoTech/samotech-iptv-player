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
    provider_id: str | None = None
    started_at: datetime | None = None
    updated_at: datetime | None = None
    watched_percentage: float = 0.0
    completed: bool = False

    def __post_init__(self) -> None:
        validate_history(
            record_id=self.id,
            item_id=self.item_id,
            item_type=self.item_type,
            provider_id=self.provider_id,
            duration_seconds=self.duration_seconds,
            position_seconds=self.position_seconds,
            watched_percentage=self.watched_percentage,
            completed=self.completed,
        )
