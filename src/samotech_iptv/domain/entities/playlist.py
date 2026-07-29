"""Playlist entity — ordered collection of channels."""
from __future__ import annotations

from dataclasses import dataclass, field

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["Playlist"]


@dataclass(frozen=True)
class Playlist:
    """A user-defined or provider-sourced ordered list of channels."""

    id: str
    name: str
    provider_id: ProviderId
    channel_ids: tuple[ChannelId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Playlist name must not be blank")
