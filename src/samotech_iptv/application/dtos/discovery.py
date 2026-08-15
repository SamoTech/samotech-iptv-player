from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "EpisodeDTO",
    "LoadSeasonEpisodesRequest",
    "LoadSeasonEpisodesResponse",
    "LoadSeriesSeasonsRequest",
    "LoadSeriesSeasonsResponse",
    "SeasonDTO",
]


def _required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValidationError(field_name, "must not be blank")


def _safe_resource_id(value: str) -> None:
    _required_text(value, "resource_id")
    if "://" in value:
        raise ValidationError("resource_id", "must not contain a resolved stream URL")


@dataclass(frozen=True)
class SeasonDTO:
    """Presentation-safe, provider-scoped identity for one series season."""

    id: str
    provider_id: str
    series_id: str
    number: int
    title: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.id, "id")
        _required_text(self.provider_id, "provider_id")
        _required_text(self.series_id, "series_id")
        if self.number < 1:
            raise ValidationError("number", "must be >= 1")
        if self.title is not None:
            _required_text(self.title, "title")


@dataclass(frozen=True)
class EpisodeDTO:
    """Presentation-safe, provider-scoped identity for one discovered episode."""

    id: str
    provider_id: str
    series_id: str
    season: int
    episode_number: int
    title: str
    resource_id: str
    duration_seconds: int | None = None
    plot: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.id, "id")
        _required_text(self.provider_id, "provider_id")
        _required_text(self.series_id, "series_id")
        _required_text(self.title, "title")
        _safe_resource_id(self.resource_id)
        if self.season < 1:
            raise ValidationError("season", "must be >= 1")
        if self.episode_number < 1:
            raise ValidationError("episode_number", "must be >= 1")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValidationError("duration_seconds", "must not be negative")


@dataclass(frozen=True)
class LoadSeriesSeasonsRequest:
    provider_id: str
    series_id: str

    def __post_init__(self) -> None:
        _required_text(self.provider_id, "provider_id")
        _required_text(self.series_id, "series_id")


@dataclass(frozen=True)
class LoadSeriesSeasonsResponse:
    seasons: Sequence[SeasonDTO] = field(default_factory=tuple)
    total: int = 0
    error: str | None = None
    unsupported: bool = False
    stale: bool = False


@dataclass(frozen=True)
class LoadSeasonEpisodesRequest:
    provider_id: str
    series_id: str
    season: int

    def __post_init__(self) -> None:
        _required_text(self.provider_id, "provider_id")
        _required_text(self.series_id, "series_id")
        if self.season < 1:
            raise ValidationError("season", "must be >= 1")


@dataclass(frozen=True)
class LoadSeasonEpisodesResponse:
    episodes: Sequence[EpisodeDTO] = field(default_factory=tuple)
    total: int = 0
    error: str | None = None
    unsupported: bool = False
    stale: bool = False
