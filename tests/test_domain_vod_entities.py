"""Tests for Movie and Series domain metadata invariants."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL


@pytest.fixture
def provider_id() -> ProviderId:
    return ProviderId("catalogue-provider")


def test_movie_accepts_complete_valid_catalogue_metadata(provider_id: ProviderId) -> None:
    movie = Movie(
        id="movie-42",
        title="The Example Movie",
        provider_id=provider_id,
        stream_id=StreamId("movie-stream-42"),
        category_id="drama",
        year=2024,
        rating=8.5,
        poster_url=URL("https://assets.example.test/movie.png"),
        plot="A test-only plot.",
    )

    assert movie.title == "The Example Movie"
    assert movie.rating == 8.5


def test_series_accepts_complete_valid_catalogue_metadata(provider_id: ProviderId) -> None:
    series = Series(
        id="series-42",
        title="The Example Series",
        provider_id=provider_id,
        category_id="drama",
        year=2024,
        rating=10.0,
        poster_url=URL("https://assets.example.test/series.png"),
        plot="A test-only plot.",
    )

    assert series.title == "The Example Series"
    assert series.rating == 10.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "Catalogue item ID"),
        ("title", " ", "Catalogue item title"),
        ("category_id", " ", "Category ID"),
        ("year", 0, "Year"),
        ("rating", -0.1, "Rating"),
        ("rating", 10.1, "Rating"),
    ],
)
def test_movie_rejects_invalid_catalogue_metadata(
    provider_id: ProviderId, field: str, value: str | int | float, message: str
) -> None:
    values: dict[str, str | int | float | ProviderId | StreamId | None] = {
        "id": "movie-42",
        "title": "The Example Movie",
        "provider_id": provider_id,
        "stream_id": StreamId("movie-stream-42"),
        "category_id": "drama",
        "year": 2024,
        "rating": 8.0,
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Movie(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "Catalogue item ID"),
        ("title", " ", "Catalogue item title"),
        ("category_id", " ", "Category ID"),
        ("year", -1, "Year"),
        ("rating", float("inf"), "Rating"),
    ],
)
def test_series_rejects_invalid_catalogue_metadata(
    provider_id: ProviderId, field: str, value: str | int | float, message: str
) -> None:
    values: dict[str, str | int | float | ProviderId | None] = {
        "id": "series-42",
        "title": "The Example Series",
        "provider_id": provider_id,
        "category_id": "drama",
        "year": 2024,
        "rating": 8.0,
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Series(**values)  # type: ignore[arg-type]
