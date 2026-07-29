"""Series entity — a VOD series (seasons + episodes)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Series"]


@dataclass(frozen=True)
class Series:
    """A VOD series (collection of seasons/episodes)."""

    id: str
    title: str
    provider_id: ProviderId
    category_id: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    poster_url: Optional[URL] = None
    plot: Optional[str] = None
