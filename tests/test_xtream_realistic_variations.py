"""Synthetic Xtream payload variations that exercise non-live compatibility boundaries."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.xtream_domain_translator import XtreamDomainTranslator

PROVIDER = ProviderId("xtream-synthetic")


MOVIE_VARIATIONS: list[dict[str, object]] = [
    {
        "stream_id": "1001",
        "name": "String-ID Movie",
        "category_id": "7",
        "container_extension": "mkv",
        "stream_icon": "https://assets.example.test/movie-1001.jpg",
        "year": "2024",
        "rating": "8.5",
        "plot": "Synthetic plot",
        "unknown_field": {"ignored": True},
    },
    {
        "stream_id": 1002,
        "name": "Missing Optional Movie",
        "container_extension": "",
        "stream_icon": None,
        "year": None,
        "rating": None,
        "plot": "",
    },
]


SERIES_VARIATIONS: list[dict[str, object]] = [
    {
        "series_id": "2001",
        "name": "String-ID Series",
        "category_id": "drama",
        "cover": "https://assets.example.test/series-2001.jpg",
        "year": "2023",
        "rating": "7.5",
        "plot": "Synthetic series plot",
    },
    {
        "series_id": 2002,
        "name": "Sparse Series",
        "cover": None,
        "rating": None,
        "plot": None,
    },
]


@pytest.mark.parametrize("record", MOVIE_VARIATIONS)
def test_movie_variations_preserve_safe_identity_and_default_extension(
    record: dict[str, object],
) -> None:
    movie = XtreamDomainTranslator.movie(record, PROVIDER)

    assert movie.id.startswith("xtream-synthetic:")
    assert movie.stream_id.value.split("|", maxsplit=1)[1].isalnum()


def test_series_variations_preserve_optional_year_and_rating() -> None:
    series = XtreamDomainTranslator.series(SERIES_VARIATIONS[0], PROVIDER)

    assert series.id == "xtream-synthetic:2001"
    assert series.year == 2023
    assert series.rating == 7.5


def test_category_family_preserves_duplicate_and_unexpected_ordering() -> None:
    records = [
        {"category_id": "z", "category_name": "Z"},
        {"category_id": "a", "category_name": "A"},
        {"category_id": "z", "category_name": "Z duplicate"},
    ]

    categories = XtreamDomainTranslator.categories(records, PROVIDER)

    assert [(category.id, category.name) for category in categories] == [
        ("z", "Z"),
        ("a", "A"),
        ("z", "Z duplicate"),
    ]


def test_empty_category_family_is_safe() -> None:
    assert XtreamDomainTranslator.categories([], PROVIDER) == []


def test_series_detail_accepts_empty_season_and_episode_lists() -> None:
    detail = {"seasons": [], "episodes": {"1": []}, "unknown": "ignored"}

    assert XtreamDomainTranslator.seasons(detail, PROVIDER, "xtream-synthetic:2001") == []
    assert XtreamDomainTranslator.episodes(detail, "xtream-synthetic:2001", 1) == []


@pytest.mark.parametrize(
    "record",
    [
        {"stream_id": "1003", "name": "Bad Rating", "rating": "not-a-number"},
        {"stream_id": "1004", "name": "Bad Year", "year": "unknown"},
        {
            "stream_id": "1005",
            "name": "Bad Poster",
            "stream_icon": "not a valid url",
        },
    ],
)
def test_malformed_optional_movie_metadata_is_ignored_safely(
    record: dict[str, object],
) -> None:
    movie = XtreamDomainTranslator.movie(record, PROVIDER)

    assert movie.title
    assert movie.year is None
    assert movie.rating is None
    assert movie.poster_url is None


@pytest.mark.parametrize(
    "record",
    [
        {"series_id": "2003", "name": "Bad Rating", "rating": "not-a-number"},
        {"series_id": "2004", "name": "Bad Poster", "cover": "not a valid url"},
    ],
)
def test_malformed_optional_series_metadata_is_ignored_safely(
    record: dict[str, object],
) -> None:
    series = XtreamDomainTranslator.series(record, PROVIDER)

    assert series.title
    assert series.year is None
    assert series.rating is None
    assert series.poster_url is None


def test_unexpected_series_detail_shape_is_rejected_safely() -> None:
    with pytest.raises(ValidationError):
        XtreamDomainTranslator.seasons({"seasons": {}}, PROVIDER, "xtream-synthetic:2001")

    with pytest.raises(ValidationError):
        XtreamDomainTranslator.episodes({"episodes": []}, "xtream-synthetic:2001", 1)
