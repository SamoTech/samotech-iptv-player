"""Episode entity — a single episode within a Series."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.stream_id import StreamId

__all__ = ["Episode"]


@dataclass(frozen=True)
class Episode:
    """A single episode belonging to a Series."""

    id: str
    series_id: str
    title: str
    stream_id: StreamId
    season: int
    episode_number: int
    duration_seconds: int | None = None
    plot: str | None = None

    def __post_init__(self) -> None:
        if self.season < 1:
            raise ValidationError("season", "Season number must be >= 1")
        if self.episode_number < 1:
            raise ValidationError("episode_number", "Episode number must be >= 1")
