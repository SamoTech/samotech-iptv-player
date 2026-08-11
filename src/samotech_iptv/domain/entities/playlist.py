"""Playlist entity — ordered collection of channels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
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
        validate_nonblank_text(self.id, field="id", label="Playlist ID")
        validate_nonblank_text(self.name, field="name", label="Playlist name")
