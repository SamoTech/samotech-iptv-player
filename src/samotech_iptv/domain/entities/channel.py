"""Channel entity — a live-TV channel available through a provider."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from samotech_iptv.core.exceptions import ValidationError
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
    category_id: Optional[str] = None
    logo_url: Optional[URL] = None
    epg_channel_id: Optional[str] = None
    number: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Channel name must not be blank")
