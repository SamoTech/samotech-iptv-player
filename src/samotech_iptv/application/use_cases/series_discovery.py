from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.discovery import (
    EpisodeDTO,
    LoadSeasonEpisodesResponse,
    LoadSeriesSeasonsResponse,
    SeasonDTO,
)
from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.discovery import (
        LoadSeasonEpisodesRequest,
        LoadSeriesSeasonsRequest,
    )
    from samotech_iptv.application.ports.provider_non_live_resolver_port import (
        ProviderSeriesDiscoveryResolverPort,
    )
    from samotech_iptv.domain.entities.episode import Episode
    from samotech_iptv.domain.entities.season import Season

__all__ = [
    "DiscoveryAttempt",
    "DiscoveryAttemptRegistry",
    "LoadSeasonEpisodes",
    "LoadSeriesSeasons",
]


@dataclass(frozen=True)
class DiscoveryAttempt:
    """One bounded asynchronous non-live discovery request."""

    generation: int
    provider_id: str
    series_id: str
    season: int | None


class DiscoveryAttemptRegistry:
    """Keep only the newest discovery request current without retaining history."""

    def __init__(self) -> None:
        self._generation = 0
        self._current: DiscoveryAttempt | None = None

    def begin(
        self, provider_id: str, series_id: str, season: int | None = None
    ) -> DiscoveryAttempt:
        """Start a discovery attempt and invalidate all older completions."""
        self._generation += 1
        self._current = DiscoveryAttempt(self._generation, provider_id, series_id, season)
        return self._current

    def is_current(self, attempt: DiscoveryAttempt) -> bool:
        """Return whether an async result may still be exposed as current data."""
        return attempt == self._current

    def invalidate(self) -> None:
        """Discard the active context after provider navigation or cancellation."""
        self._generation += 1
        self._current = None


class LoadSeriesSeasons:
    """Load safe seasons through a capability-checked provider-neutral boundary."""

    def __init__(
        self,
        provider_resolver: ProviderSeriesDiscoveryResolverPort,
        attempts: DiscoveryAttemptRegistry | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._attempts = attempts or DiscoveryAttemptRegistry()

    @property
    def attempts(self) -> DiscoveryAttemptRegistry:
        """Expose bounded invalidation for future presentation composition."""
        return self._attempts

    async def execute(self, request: LoadSeriesSeasonsRequest) -> LoadSeriesSeasonsResponse:
        """Return the latest provider-scoped seasons or a safe controlled result."""
        attempt = self._attempts.begin(request.provider_id, request.series_id)
        try:
            provider = self._provider_resolver.resolve_series_detail_provider(request.provider_id)
            seasons = tuple(await provider.load_seasons(request.series_id))
            response = LoadSeriesSeasonsResponse(
                seasons=tuple(self._season_dto(season, request) for season in seasons),
                total=len(seasons),
            )
        except ProviderError:
            response = LoadSeriesSeasonsResponse(unsupported=True)
        except Exception:
            response = LoadSeriesSeasonsResponse(error="Unable to load seasons")
        if not self._attempts.is_current(attempt):
            return LoadSeriesSeasonsResponse(stale=True)
        return response

    @staticmethod
    def _season_dto(season: Season, request: LoadSeriesSeasonsRequest) -> SeasonDTO:
        if season.provider_id.value != request.provider_id or season.series_id != request.series_id:
            raise ProviderError("Provider returned mismatched series season")
        return SeasonDTO(
            id=season.id,
            provider_id=season.provider_id.value,
            series_id=season.series_id,
            number=season.number,
            title=season.title,
        )


class LoadSeasonEpisodes:
    """Load safe episodes through a capability-checked provider-neutral boundary."""

    def __init__(
        self,
        provider_resolver: ProviderSeriesDiscoveryResolverPort,
        attempts: DiscoveryAttemptRegistry | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._attempts = attempts or DiscoveryAttemptRegistry()

    @property
    def attempts(self) -> DiscoveryAttemptRegistry:
        """Expose bounded invalidation for future presentation composition."""
        return self._attempts

    async def execute(self, request: LoadSeasonEpisodesRequest) -> LoadSeasonEpisodesResponse:
        """Return the latest provider-scoped episodes or a safe controlled result."""
        attempt = self._attempts.begin(request.provider_id, request.series_id, request.season)
        try:
            provider = self._provider_resolver.resolve_series_detail_provider(request.provider_id)
            episodes = tuple(await provider.load_episodes(request.series_id, request.season))
            response = LoadSeasonEpisodesResponse(
                episodes=tuple(self._episode_dto(episode, request) for episode in episodes),
                total=len(episodes),
            )
        except ProviderError:
            response = LoadSeasonEpisodesResponse(unsupported=True)
        except Exception:
            response = LoadSeasonEpisodesResponse(error="Unable to load episodes")
        if not self._attempts.is_current(attempt):
            return LoadSeasonEpisodesResponse(stale=True)
        return response

    @staticmethod
    def _episode_dto(episode: Episode, request: LoadSeasonEpisodesRequest) -> EpisodeDTO:
        if episode.series_id != request.series_id or episode.season != request.season:
            raise ProviderError("Provider returned mismatched series episode")
        return EpisodeDTO(
            id=episode.id,
            provider_id=request.provider_id,
            series_id=episode.series_id,
            season=episode.season,
            episode_number=episode.episode_number,
            title=episode.title,
            resource_id=episode.stream_id.value,
            duration_seconds=episode.duration_seconds,
            plot=episode.plot,
        )
