"""Channel entity — a live-TV channel available through a provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.stream_id import StreamId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Channel"]


@dataclass(frozen=True)
class Channel:
    """A live-TV channel available from a provider."""

    id: ChannelId
    name: str
    provider_id: ProviderId
    stream_id: StreamId
    category_id: str | None = None
    logo_url: URL | None = None
    epg_channel_id: str | None = None
    number: int | None = None

    def __post_init__(self) -> None:
        validate_nonblank_text(self.name, field="name", label="Channel name")
        if self.category_id is not None:
            validate_nonblank_text(
                self.category_id,
                field="category_id",
                label="Category ID",
                when_supplied=True,
            )
        if self.epg_channel_id is not None:
            validate_nonblank_text(
                self.epg_channel_id,
                field="epg_channel_id",
                label="EPG channel ID",
                when_supplied=True,
            )
