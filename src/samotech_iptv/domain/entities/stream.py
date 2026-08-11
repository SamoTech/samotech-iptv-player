"""Stream entity — a playable media stream URI with metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.stream_id import StreamId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Stream"]


@dataclass(frozen=True)
class Stream:
    """A playable media stream URI with associated metadata."""

    id: StreamId
    url: URL
    container: str = "ts"
    codec: str | None = None
    bitrate_kbps: int | None = None
    is_encrypted: bool = False
