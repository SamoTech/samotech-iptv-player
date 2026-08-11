"""Stream entity — a playable media stream URI with metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

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

    def __post_init__(self) -> None:
        if not self.container.strip():
            raise ValidationError("container", "Stream container must not be blank")
        if self.codec is not None and not self.codec.strip():
            raise ValidationError("codec", "Stream codec must not be blank when supplied")
        if self.bitrate_kbps is not None and self.bitrate_kbps <= 0:
            raise ValidationError(
                "bitrate_kbps",
                "Stream bitrate must be positive when supplied",
            )
