"""Application tests for capability-driven non-live catalogue browsing."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.content import BrowseContentRequest, ContentType
from samotech_iptv.application.use_cases.browse_content import BrowseContent
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_content_resolver_port import (
        ProviderContentResolverPort,
    )


class FakeVodProvider:
    def __init__(self, movies: list[Movie]) -> None:
        self.movies = movies
        self.calls = 0

    async def load_movies(self) -> list[Movie]:
        self.calls += 1
        return self.movies


class FakeSeriesProvider:
    def __init__(self, series: list[Series]) -> None:
        self.series = series
        self.calls = 0

    async def load_series(self) -> list[Series]:
        self.calls += 1
        return self.series


class FakeContentResolver:
    def __init__(self, vod: FakeVodProvider, series: FakeSeriesProvider) -> None:
        self.vod = vod
        self.series = series
        self.vod_ids: list[str] = []
        self.series_ids: list[str] = []

    def resolve_vod_provider(self, provider_id: str) -> FakeVodProvider:
        self.vod_ids.append(provider_id)
        return self.vod

    def resolve_series_provider(self, provider_id: str) -> FakeSeriesProvider:
        self.series_ids.append(provider_id)
        return self.series


@pytest.mark.asyncio
async def test_browse_content_maps_existing_movie_identity_without_channel_dto_overload() -> None:
    movie = Movie(
        id="movie-1",
        title="The Example Film",
        provider_id=ProviderId("xtream-demo"),
        stream_id=StreamId("movie-stream-1"),
        category_id="drama",
        year=2024,
        rating=8.5,
        plot="A bounded test fixture.",
        duration_seconds=3600,
        genre="Drama",
        director="Example Director",
        backdrop_url=None,
        container_extension="mp4",
    )
    resolver = FakeContentResolver(FakeVodProvider([movie]), FakeSeriesProvider([]))

    response = await BrowseContent(cast("ProviderContentResolverPort", resolver)).execute(
        BrowseContentRequest(provider_id="xtream-demo", content_type=ContentType.MOVIE)
    )

    assert response.error is None
    assert response.unsupported is False
    assert response.total == 1
    assert response.items[0].id == "movie-1"
    assert response.items[0].stream_id == "movie-stream-1"
    assert response.items[0].content_type is ContentType.MOVIE
    assert response.items[0].duration_seconds == 3600
    assert response.items[0].genre == "Drama"
    assert response.items[0].director == "Example Director"
    assert response.items[0].container_extension == "mp4"
    assert resolver.vod_ids == ["xtream-demo"]
    assert resolver.vod.calls == 1


@pytest.mark.asyncio
async def test_browse_content_maps_existing_series_identity_without_playback_claim() -> None:
    series = Series(
        id="series-1",
        title="The Example Series",
        provider_id=ProviderId("xtream-demo"),
        category_id="drama",
        year=2023,
        rating=7.5,
        genre="Drama",
        season_count=2,
        episode_count=16,
    )
    resolver = FakeContentResolver(FakeVodProvider([]), FakeSeriesProvider([series]))

    response = await BrowseContent(cast("ProviderContentResolverPort", resolver)).execute(
        BrowseContentRequest(provider_id="xtream-demo", content_type=ContentType.SERIES)
    )

    assert response.error is None
    assert response.unsupported is False
    assert response.items[0].id == "series-1"
    assert response.items[0].stream_id is None
    assert response.items[0].content_type is ContentType.SERIES
    assert response.items[0].genre == "Drama"
    assert response.items[0].season_count == 2
    assert response.items[0].episode_count == 16
    assert resolver.series_ids == ["xtream-demo"]
    assert resolver.series.calls == 1


@pytest.mark.asyncio
async def test_browse_content_reports_episode_as_unsupported_without_provider_call() -> None:
    vod = FakeVodProvider([])
    series = FakeSeriesProvider([])
    resolver = FakeContentResolver(vod, series)

    response = await BrowseContent(cast("ProviderContentResolverPort", resolver)).execute(
        BrowseContentRequest(provider_id="xtream-demo", content_type=ContentType.EPISODE)
    )

    assert response.unsupported is True
    assert response.items == []
    assert vod.calls == 0
    assert series.calls == 0


@pytest.mark.asyncio
async def test_browse_content_sanitises_unsupported_provider_failure() -> None:
    class UnsupportedResolver(FakeContentResolver):
        def resolve_vod_provider(self, provider_id: str) -> FakeVodProvider:
            raise ProviderError("credential-bearing provider failure")

    response = await BrowseContent(
        cast(
            "ProviderContentResolverPort",
            UnsupportedResolver(FakeVodProvider([]), FakeSeriesProvider([])),
        )
    ).execute(BrowseContentRequest(provider_id="xtream-demo", content_type=ContentType.MOVIE))

    assert response.unsupported is True
    assert response.error is None
