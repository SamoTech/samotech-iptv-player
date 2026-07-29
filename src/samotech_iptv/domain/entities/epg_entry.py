"""EPGEntry entity — a single Electronic Programme Guide entry."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from samotech_iptv.core.exceptions import ValidationError
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
    description: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValidationError("end", "EPG end time must be after start time")
