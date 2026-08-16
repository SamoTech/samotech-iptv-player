"""CatchupEvent — a normalized archived programme event."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from datetime import datetime

    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["CatchupEvent"]


@dataclass(frozen=True)
class CatchupEvent:
    """An optional provider-supplied catch-up event without a resolved private URL."""

    id: str
    provider_id: ProviderId
    channel_id: ChannelId
    title: str
    start: datetime
    end: datetime
    description: str | None = None
    stream_id: str | None = None

    def __post_init__(self) -> None:
        validate_nonblank_text(self.id, field="id", label="Catch-up event ID")
        validate_nonblank_text(self.title, field="title", label="Catch-up event title")
        if self.end <= self.start:
            raise ValidationError("end", "Catch-up event end time must be after start time")
        if self.stream_id is not None:
            validate_nonblank_text(
                self.stream_id,
                field="stream_id",
                label="Catch-up stream ID",
                when_supplied=True,
            )
