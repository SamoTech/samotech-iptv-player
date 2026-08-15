from __future__ import annotations

import asyncio

import pytest

from samotech_iptv.application.dtos.discovery import (
    EpisodeDTO,
    LoadSeasonEpisodesRequest,
    LoadSeriesSeasonsRequest,
)
from samotech_iptv.application.dtos.playback import PlaybackTarget
from samotech_iptv.application.use_cases.play_playback_target import PlaybackAttemptRegistry
from samotech_iptv.application.use_cases.series_discovery import (
    DiscoveryAttemptRegistry,
    LoadSeasonEpisodes,
    LoadSeriesSeasons,
)
from samotech_iptv.core.exceptions import ProviderError, ValidationError
from samotech_iptv.domain.entities.episode import Episode
from samotech_iptv.domain.entities.season import Season
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId


def season(provider_id: str, series_id: str, number: int) -> Season:
    return Season(
        id=f"{provider_id}:{series_id}:season-{number}",
        provider_id=ProviderId(provider_id),
        series_id=series_id,
        number=number,
        title=f"Season {number}",
    )


def episode(provider_id: str, series_id: str, season_number: int, number: int) -> Episode:
    return Episode(
        id=f"{provider_id}:{series_id}:season-{season_number}:episode-{number}",
        series_id=series_id,
        title=f"Episode {number}",
        stream_id=StreamId(f"episode-resource-{number}"),
        season=season_number,
        episode_number=number,
        duration_seconds=1_800,
        plot="Synthetic test fixture.",
    )


class ControlledSeriesDetailProvider:
    """Fake provider whose discovery completions are deliberately ordered by tests."""

    def __init__(self) -> None:
        self.season_futures: dict[str, asyncio.Future[list[Season]]] = {}
        self.episode_futures: dict[tuple[str, int], asyncio.Future[list[Episode]]] = {}

    def pending_seasons(self, series_id: str) -> asyncio.Future[list[Season]]:
        future = asyncio.get_running_loop().create_future()
        self.season_futures[series_id] = future
        return future

    def pending_episodes(self, series_id: str, season_number: int) -> asyncio.Future[list[Episode]]:
        future = asyncio.get_running_loop().create_future()
        self.episode_futures[(series_id, season_number)] = future
        return future

    async def load_seasons(self, series_id: str) -> list[Season]:
        return await self.season_futures[series_id]

    async def load_episodes(self, series_id: str, season_number: int) -> list[Episode]:
        return await self.episode_futures[(series_id, season_number)]


class ControlledResolver:
    """Provider-neutral resolver fake that exposes no credentials or raw payloads."""

    def __init__(self, providers: dict[str, ControlledSeriesDetailProvider]) -> None:
        self.providers = providers
        self.provider_ids: list[str] = []

    def resolve_series_detail_provider(self, provider_id: str) -> ControlledSeriesDetailProvider:
        self.provider_ids.append(provider_id)
        try:
            return self.providers[provider_id]
        except KeyError as exc:
            raise ProviderError("Provider does not support series details") from exc


@pytest.mark.asyncio
async def test_series_season_discovery_maps_provider_scoped_identity() -> None:
    provider = ControlledSeriesDetailProvider()
    provider.pending_seasons("series-a").set_result([season("provider-a", "series-a", 1)])
    resolver = ControlledResolver({"provider-a": provider})

    response = await LoadSeriesSeasons(resolver).execute(
        LoadSeriesSeasonsRequest("provider-a", "series-a")
    )

    assert response.error is None
    assert response.unsupported is False
    assert response.stale is False
    assert response.total == 1
    assert response.seasons[0].id == "provider-a:series-a:season-1"
    assert response.seasons[0].provider_id == "provider-a"
    assert response.seasons[0].series_id == "series-a"
    assert response.seasons[0].number == 1


@pytest.mark.asyncio
async def test_episode_discovery_maps_safe_provider_scoped_identity() -> None:
    provider = ControlledSeriesDetailProvider()
    provider.pending_episodes("series-a", 1).set_result([episode("provider-a", "series-a", 1, 2)])
    resolver = ControlledResolver({"provider-a": provider})

    response = await LoadSeasonEpisodes(resolver).execute(
        LoadSeasonEpisodesRequest("provider-a", "series-a", 1)
    )

    assert response.error is None
    assert response.unsupported is False
    assert response.stale is False
    assert response.total == 1
    assert response.episodes[0].id == "provider-a:series-a:season-1:episode-2"
    assert response.episodes[0].resource_id == "episode-resource-2"
    assert response.episodes[0].series_id == "series-a"
    assert response.episodes[0].season == 1
    assert response.episodes[0].episode_number == 2


@pytest.mark.asyncio
async def test_series_detail_capability_is_controlled_unsupported_without_provider_call() -> None:
    resolver = ControlledResolver({})

    seasons = await LoadSeriesSeasons(resolver).execute(
        LoadSeriesSeasonsRequest("unsupported", "series-a")
    )
    episodes = await LoadSeasonEpisodes(resolver).execute(
        LoadSeasonEpisodesRequest("unsupported", "series-a", 1)
    )

    assert seasons.unsupported is True
    assert seasons.seasons == ()
    assert episodes.unsupported is True
    assert episodes.episodes == ()
    assert resolver.provider_ids == ["unsupported", "unsupported"]


@pytest.mark.asyncio
async def test_series_a_then_series_b_discards_late_a_result() -> None:
    provider = ControlledSeriesDetailProvider()
    registry = DiscoveryAttemptRegistry()
    use_case = LoadSeriesSeasons(ControlledResolver({"provider-a": provider}), registry)
    a_future = provider.pending_seasons("series-a")
    b_future = provider.pending_seasons("series-b")

    a_task = asyncio.create_task(
        use_case.execute(LoadSeriesSeasonsRequest("provider-a", "series-a"))
    )
    await asyncio.sleep(0)
    b_task = asyncio.create_task(
        use_case.execute(LoadSeriesSeasonsRequest("provider-a", "series-b"))
    )
    await asyncio.sleep(0)
    b_future.set_result([season("provider-a", "series-b", 1)])
    b_response = await b_task
    a_future.set_result([season("provider-a", "series-a", 1)])
    a_response = await a_task

    assert b_response.stale is False
    assert b_response.seasons[0].series_id == "series-b"
    assert a_response.stale is True
    assert a_response.seasons == ()


@pytest.mark.asyncio
async def test_provider_a_then_provider_b_discards_late_a_episode_result() -> None:
    provider_a = ControlledSeriesDetailProvider()
    provider_b = ControlledSeriesDetailProvider()
    registry = DiscoveryAttemptRegistry()
    use_case = LoadSeasonEpisodes(
        ControlledResolver({"provider-a": provider_a, "provider-b": provider_b}), registry
    )
    a_future = provider_a.pending_episodes("series-a", 1)
    b_future = provider_b.pending_episodes("series-b", 1)

    a_task = asyncio.create_task(
        use_case.execute(LoadSeasonEpisodesRequest("provider-a", "series-a", 1))
    )
    await asyncio.sleep(0)
    b_task = asyncio.create_task(
        use_case.execute(LoadSeasonEpisodesRequest("provider-b", "series-b", 1))
    )
    await asyncio.sleep(0)
    b_future.set_result([episode("provider-b", "series-b", 1, 1)])
    b_response = await b_task
    a_future.set_result([episode("provider-a", "series-a", 1, 1)])
    a_response = await a_task

    assert b_response.stale is False
    assert b_response.episodes[0].provider_id == "provider-b"
    assert a_response.stale is True
    assert a_response.episodes == ()


@pytest.mark.asyncio
async def test_season_a_then_season_b_discards_late_a_episode_result() -> None:
    provider = ControlledSeriesDetailProvider()
    use_case = LoadSeasonEpisodes(ControlledResolver({"provider-a": provider}))
    first_future = provider.pending_episodes("series-a", 1)
    second_future = provider.pending_episodes("series-a", 2)

    first_task = asyncio.create_task(
        use_case.execute(LoadSeasonEpisodesRequest("provider-a", "series-a", 1))
    )
    await asyncio.sleep(0)
    second_task = asyncio.create_task(
        use_case.execute(LoadSeasonEpisodesRequest("provider-a", "series-a", 2))
    )
    await asyncio.sleep(0)
    second_future.set_result([episode("provider-a", "series-a", 2, 1)])
    second_response = await second_task
    first_future.set_result([episode("provider-a", "series-a", 1, 1)])
    first_response = await first_task

    assert second_response.stale is False
    assert second_response.episodes[0].season == 2
    assert first_response.stale is True


@pytest.mark.asyncio
async def test_discovery_projects_dynamic_season_and_episode_collections() -> None:
    provider = ControlledSeriesDetailProvider()
    seasons = [season("provider-a", "series-a", number) for number in range(1, 1_001)]
    episodes = [episode("provider-a", "series-a", 1, number) for number in range(1, 5_001)]
    provider.pending_seasons("series-a").set_result(seasons)
    provider.pending_episodes("series-a", 1).set_result(episodes)
    resolver = ControlledResolver({"provider-a": provider})

    season_response = await LoadSeriesSeasons(resolver).execute(
        LoadSeriesSeasonsRequest("provider-a", "series-a")
    )
    episode_response = await LoadSeasonEpisodes(resolver).execute(
        LoadSeasonEpisodesRequest("provider-a", "series-a", 1)
    )

    assert season_response.total == 1_000
    assert season_response.seasons[0].number == 1
    assert season_response.seasons[-1].number == 1_000
    assert episode_response.total == 5_000
    assert episode_response.episodes[0].episode_number == 1
    assert episode_response.episodes[-1].episode_number == 5_000


def test_discovery_registry_invalidates_late_completion_without_retaining_history() -> None:
    registry = DiscoveryAttemptRegistry()
    first = registry.begin("provider-a", "series-a", 1)
    registry.invalidate()
    second = registry.begin("provider-b", "series-b", 2)

    assert first.generation == 1
    assert not registry.is_current(first)
    assert second.generation == 3
    assert registry.is_current(second)


def test_movie_episode_cross_selection_uses_one_playback_generation() -> None:
    registry = PlaybackAttemptRegistry()
    movie_attempt = registry.begin(PlaybackTarget.movie("provider-a", "movie-a", "movie-resource"))
    episode_attempt = registry.begin(
        PlaybackTarget.episode("provider-a", "episode-a", "episode-resource", "series-a", 1, 1)
    )

    assert not registry.is_current(movie_attempt)
    assert registry.is_current(episode_attempt)
    next_movie_attempt = registry.begin(
        PlaybackTarget.movie("provider-a", "movie-b", "movie-resource-b")
    )
    assert not registry.is_current(episode_attempt)
    assert registry.is_current(next_movie_attempt)


@pytest.mark.parametrize(
    ("factory", "field"),
    [
        (
            lambda: PlaybackTarget.movie("provider-a", "movie-a", "https://example.invalid/movie"),
            "resource_id",
        ),
        (
            lambda: PlaybackTarget.episode(
                "provider-a", "episode-a", "https://example.invalid/episode", "series-a", 1, 1
            ),
            "resource_id",
        ),
        (
            lambda: EpisodeDTO(
                id="episode-a",
                provider_id="provider-a",
                series_id="series-a",
                season=1,
                episode_number=1,
                title="Example",
                resource_id="https://example.invalid/episode",
            ),
            "resource_id",
        ),
    ],
)
def test_non_live_targets_and_dtos_reject_raw_resolved_urls(factory: object, field: str) -> None:
    with pytest.raises(ValidationError, match=f"^{field}:"):
        factory()  # type: ignore[operator]
