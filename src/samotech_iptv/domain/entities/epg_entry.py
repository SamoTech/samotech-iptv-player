"""EPGEntry entity — a single Electronic Programme Guide entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from datetime import datetime

    from samotech_iptv.domain.value_objects.channel_id import ChannelId

__all__ = ["EPGEntry"]


@dataclass(frozen=True)
class EPGEntry:
    """A single Electronic Programme Guide entry."""

    id: str
    channel_id: ChannelId
    title: str
    start: datetime
    end: datetime
    description: str | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        validate_nonblank_text(self.id, field="id", label="EPG entry ID")
        validate_nonblank_text(self.title, field="title", label="EPG entry title")
        if self.end <= self.start:
            raise ValidationError("end", "EPG end time must be after start time")
