"""Episode entity — a single episode within a Series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

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
        validate_nonblank_text(self.id, field="id", label="Episode ID")
        validate_nonblank_text(self.series_id, field="series_id", label="Series ID")
        validate_nonblank_text(self.title, field="title", label="Episode title")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValidationError("duration_seconds", "Episode duration must not be negative")
        if self.season < 1:
            raise ValidationError("season", "Season number must be >= 1")
        if self.episode_number < 1:
            raise ValidationError("episode_number", "Episode number must be >= 1")
