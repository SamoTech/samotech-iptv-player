"""Movie entity — a VOD movie."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_catalogue_metadata

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
    duration_seconds: int | None = None
    genre: str | None = None
    director: str | None = None
    cast: str | None = None
    country: str | None = None
    release_date: str | None = None
    backdrop_url: URL | None = None
    container_extension: str | None = None

    def __post_init__(self) -> None:
        validate_catalogue_metadata(
            item_id=self.id,
            title=self.title,
            category_id=self.category_id,
            year=self.year,
            rating=self.rating,
        )
