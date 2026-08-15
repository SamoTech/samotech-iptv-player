from __future__ import annotations

import pytest

from samotech_iptv.application.dtos import LoadMovieDetailsRequest
from samotech_iptv.application.ports.provider_capabilities import MovieDetailProvider
from samotech_iptv.application.use_cases.load_movie_details import LoadMovieDetails
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId


class FixedMovieProvider(MovieDetailProvider):
    """Synthetic VOD-detail provider for application-boundary tests."""

    def __init__(self, movie: Movie | None = None, error: Exception | None = None) -> None:
        self.movie = movie
        self.error = error
        self.movie_ids: list[str] = []

    async def load_movie_details(self, movie_id: str) -> Movie:
        self.movie_ids.append(movie_id)
        if self.error is not None:
            raise self.error
        assert self.movie is not None
        return self.movie


class FixedMovieResolver:
    """Resolve the synthetic provider or raise a controlled capability error."""

    def __init__(self, provider: FixedMovieProvider | None = None) -> None:
        self.provider = provider

    def resolve_movie_detail_provider(self, _: str) -> MovieDetailProvider:
        if self.provider is None:
            raise ProviderError("Provider does not support movie details")
        return self.provider


def _movie() -> Movie:
    return Movie(
        id="provider-a:42",
        title="Example Movie",
        provider_id=ProviderId("provider-a"),
        stream_id=StreamId("42|mp4"),
        year=2024,
        rating=4.5,
        plot="Synthetic detail metadata",
    )


@pytest.mark.asyncio
async def test_movie_detail_projects_existing_canonical_metadata_safely() -> None:
    provider = FixedMovieProvider(_movie())
    response = await LoadMovieDetails(FixedMovieResolver(provider)).execute(
        LoadMovieDetailsRequest("provider-a", "provider-a:42")
    )

    assert response.error is None
    assert response.unsupported is False
    assert response.item is not None
    assert response.item.title == "Example Movie"
    assert response.item.stream_id == "42|mp4"
    assert provider.movie_ids == ["provider-a:42"]


@pytest.mark.asyncio
async def test_movie_detail_reports_unsupported_without_provider_fallback() -> None:
    response = await LoadMovieDetails(FixedMovieResolver()).execute(
        LoadMovieDetailsRequest("provider-a", "provider-a:42")
    )

    assert response.item is None
    assert response.unsupported is True
    assert response.error is None


@pytest.mark.asyncio
async def test_movie_detail_hides_unexpected_provider_failures() -> None:
    response = await LoadMovieDetails(
        FixedMovieResolver(FixedMovieProvider(error=RuntimeError("synthetic detail failure")))
    ).execute(LoadMovieDetailsRequest("provider-a", "provider-a:42"))

    assert response.item is None
    assert response.unsupported is False
    assert response.error == "Unable to load movie details"
