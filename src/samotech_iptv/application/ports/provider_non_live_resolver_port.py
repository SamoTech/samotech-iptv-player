from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        EpisodePlaybackProvider,
        MoviePlaybackProvider,
        SeriesDetailProvider,
    )

__all__ = [
    "ProviderNonLivePlaybackResolverPort",
    "ProviderSeriesDiscoveryResolverPort",
]


class ProviderNonLivePlaybackResolverPort(ABC):
    """Resolve optional non-live playback capabilities without changing Live resolver ABI."""

    @abstractmethod
    def resolve_movie_playback_provider(self, provider_id: str) -> MoviePlaybackProvider:
        """Return a movie-resolution provider or raise a controlled provider error."""
        ...

    @abstractmethod
    def resolve_episode_playback_provider(self, provider_id: str) -> EpisodePlaybackProvider:
        """Return an episode-resolution provider or raise a controlled provider error."""
        ...


class ProviderSeriesDiscoveryResolverPort(ABC):
    """Resolve optional series-detail discovery without changing catalogue resolver ABI."""

    @abstractmethod
    def resolve_series_detail_provider(self, provider_id: str) -> SeriesDetailProvider:
        """Return a series-detail provider or raise a controlled provider error."""
        ...
