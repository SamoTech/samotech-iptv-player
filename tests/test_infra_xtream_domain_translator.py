"""Tests for Xtream live-channel DTO translation."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.xtream_domain_translator import XtreamDomainTranslator


def test_category_maps_xtream_group_record() -> None:
    category = XtreamDomainTranslator.category(
        {"category_id": "drama", "category_name": "Drama", "parent_id": "premium"},
        ProviderId("xtream-demo"),
    )

    assert category.id == "drama"
    assert category.name == "Drama"
    assert category.parent_id == "premium"


def test_movie_maps_xtream_vod_stream_record() -> None:
    movie = XtreamDomainTranslator.movie(
        {
            "stream_id": 42,
            "name": "Example Movie",
            "category_id": "movies",
            "stream_icon": "https://assets.example.test/movie.jpg",
            "plot": "A deterministic VOD fixture.",
        },
        ProviderId("xtream-demo"),
    )

    assert movie.id == "xtream-demo:42"
    assert movie.stream_id.value == "42|mp4"
    assert movie.category_id == "movies"


def test_series_maps_xtream_series_record() -> None:
    series = XtreamDomainTranslator.series(
        {
            "series_id": 84,
            "name": "Example Series",
            "category_id": "drama",
            "cover": "https://assets.example.test/series.jpg",
            "plot": "A deterministic series fixture.",
        },
        ProviderId("xtream-demo"),
    )

    assert series.id == "xtream-demo:84"
    assert series.category_id == "drama"
    assert series.poster_url is not None


def test_series_detail_maps_seasons_and_episodes_to_opaque_canonical_identity() -> None:
    detail = {
        "seasons": [{"season_number": 1, "name": "Season One"}],
        "episodes": {
            "1": [
                {
                    "id": 501,
                    "episode_num": 1,
                    "title": "Pilot",
                    "container_extension": "mp4",
                    "info": {"duration_secs": 1200, "plot": "Episode metadata"},
                }
            ]
        },
    }

    seasons = XtreamDomainTranslator.seasons(detail, ProviderId("xtream-demo"), "xtream-demo:84")
    episodes = XtreamDomainTranslator.episodes(detail, "xtream-demo:84", 1)

    assert [(season.id, season.number) for season in seasons] == [("xtream-demo:84:season:1", 1)]
    assert episodes[0].id == "xtream-demo:84:episode:501"
    assert episodes[0].stream_id.value == "501|mp4"
    assert episodes[0].duration_seconds == 1200


def test_non_live_playback_resource_rejects_invalid_extension_or_shape() -> None:
    with pytest.raises(ValidationError):
        XtreamDomainTranslator.playback_resource("42", "m3u8?unsafe")
    with pytest.raises(ValidationError):
        XtreamDomainTranslator.split_playback_resource("42")


def test_epg_entry_maps_xtream_short_epg_record() -> None:
    entries = XtreamDomainTranslator.epg_entries(
        [
            {
                "id": "guide-84",
                "title": "RXhhbXBsZSBQcm9ncmFtbWU=",
                "description": "QSBkZXRlcm1pbmlzdGljIEVQRyBmaXh0dXJlLg==",
                "start_timestamp": 1_700_000_000,
                "stop_timestamp": 1_700_003_600,
            }
        ],
        ChannelId("xtream-demo:101"),
    )

    assert entries[0].id == "guide-84"
    assert entries[0].title == "Example Programme"
    assert entries[0].description == "A deterministic EPG fixture."
    assert entries[0].start.tzinfo is not None


def test_channel_maps_xtream_live_stream_record() -> None:
    channel = XtreamDomainTranslator.channel(
        {
            "stream_id": 101,
            "name": "News HD",
            "stream_icon": "https://assets.example.test/news.png",
            "category_id": 7,
            "epg_channel_id": "news.example",
            "num": "12",
        },
        ProviderId("xtream-demo"),
    )

    assert channel.id.value == "xtream-demo:101"
    assert channel.stream_id.value == "101"
    assert channel.number == 12


@pytest.mark.parametrize(
    "logo",
    [
        "",
        "https://assets.example.test/logo.png",
        "https://docdog.top/logo/countries/ar/\u00a0ALFADY_TV.png",
        "https://lo1.in/sp/LA 1 FHD.png",
    ],
)
def test_channel_tolerates_optional_logo_metadata(logo: str) -> None:
    channel = XtreamDomainTranslator.channel(
        {"stream_id": 101, "name": "News", "stream_icon": logo},
        ProviderId("xtream-demo"),
    )

    if logo == "https://assets.example.test/logo.png":
        assert str(channel.logo_url) == logo
    else:
        assert channel.logo_url is None


def test_channel_keeps_valid_channels_when_one_logo_is_invalid() -> None:
    records = [
        {"stream_id": 1, "name": "Good", "stream_icon": "https://assets.example.test/good.png"},
        {"stream_id": 2, "name": "Bad Logo", "stream_icon": "https://lo1.in/sp/LA 1 FHD.png"},
    ]

    channels = [
        XtreamDomainTranslator.channel(record, ProviderId("xtream-demo"), record_index=index)
        for index, record in enumerate(records, start=1)
    ]

    assert [channel.name for channel in channels] == ["Good", "Bad Logo"]
    assert channels[0].logo_url is not None
    assert channels[1].logo_url is None


@pytest.mark.parametrize(
    "record", [{"name": "News"}, {"stream_id": 1}, {"stream_id": 1, "name": "News", "num": "x"}]
)
def test_channel_rejects_malformed_xtream_live_stream(record: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        XtreamDomainTranslator.channel(record, ProviderId("xtream-demo"))
