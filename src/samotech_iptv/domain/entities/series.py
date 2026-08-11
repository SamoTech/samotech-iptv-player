"""Series entity — a VOD series (seasons + episodes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_catalogue_metadata

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Series"]


@dataclass(frozen=True)
class Series:
    """A VOD series (collection of seasons/episodes)."""

    id: str
    title: str
    provider_id: ProviderId
    category_id: str | None = None
    year: int | None = None
    rating: float | None = None
    poster_url: URL | None = None
    plot: str | None = None

    def __post_init__(self) -> None:
        validate_catalogue_metadata(
            item_id=self.id,
            title=self.title,
            category_id=self.category_id,
            year=self.year,
            rating=self.rating,
        )
