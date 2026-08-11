"""Movie entity — a VOD movie."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.stream_id import StreamId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Movie"]


@dataclass(frozen=True)
class Movie:
    """A VOD movie entry."""

    id: str
    title: str
    provider_id: ProviderId
    stream_id: StreamId
    category_id: str | None = None
    year: int | None = None
    rating: float | None = None
    poster_url: URL | None = None
    plot: str | None = None
