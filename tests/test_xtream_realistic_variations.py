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
    {
        "stream_id": 1003,
        "name": "Unusual Container Movie",
        "container_extension": "webm",
        "stream_icon": "https://assets.example.test/movie-1003.webp",
        "year": 2022,
        "rating": 6,
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


def test_unusual_container_extension_is_preserved_when_safe() -> None:
    movie = XtreamDomainTranslator.movie(MOVIE_VARIATIONS[2], PROVIDER)

    assert movie.stream_id.value == "1003|webm"


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


def test_series_detail_skips_malformed_and_duplicate_nested_records() -> None:
    detail = {
        "seasons": [
            {"season_number": 1, "name": "Season One"},
            {"season_number": 1, "name": "Duplicate Season"},
            {"name": "Missing Season Number"},
        ],
        "episodes": {
            "1": [
                {"id": 501, "episode_num": 1, "title": "Pilot"},
                {"id": 501, "episode_num": 1, "title": "Duplicate Pilot"},
                {"episode_num": 2, "title": "Missing Episode ID"},
            ]
        },
    }

    seasons = XtreamDomainTranslator.seasons(detail, PROVIDER, "xtream-synthetic:2001")
    episodes = XtreamDomainTranslator.episodes(detail, "xtream-synthetic:2001", 1)

    assert [(season.number, season.title) for season in seasons] == [(1, "Season One")]
    assert [(episode.id, episode.episode_number) for episode in episodes] == [
        ("xtream-synthetic:2001:episode:501", 1)
    ]


def test_unicode_and_list_shaped_artwork_are_translated_without_secret_payloads() -> None:
    movie = XtreamDomainTranslator.movie(
        {
            "stream_id": "9001",
            "name": "فيلم عربي – اختبار",
            "stream_icon": ["", "https://assets.example.test/poster-9001.jpg"],
            "backdrop_path": ["https://assets.example.test/backdrop-9001.jpg"],
            "year": "2026",
            "rating": "9.0",
        },
        PROVIDER,
    )

    assert movie.title == "فيلم عربي – اختبار"
    assert str(movie.poster_url) == "https://assets.example.test/poster-9001.jpg"
    assert str(movie.backdrop_url) == "https://assets.example.test/backdrop-9001.jpg"


def test_sparse_episode_defaults_title_and_preserves_opaque_identity() -> None:
    detail = {
        "episodes": {
            "2": [
                {
                    "id": "9002",
                    "episode_num": "2",
                    "info": {"plot": "مرحبا"},
                }
            ]
        }
    }

    episodes = XtreamDomainTranslator.episodes(detail, "xtream-synthetic:2001", 2)

    assert episodes[0].id == "xtream-synthetic:2001:episode:9002"
    assert episodes[0].title == "Episode 2"
    assert episodes[0].plot == "مرحبا"
    assert episodes[0].stream_id.value == "9002|mp4"
