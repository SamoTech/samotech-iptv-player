"""Tests for Xtream live-channel DTO translation."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.xtream_domain_translator import XtreamDomainTranslator


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
    assert movie.stream_id.value == "42"
    assert movie.category_id == "movies"


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
    "record", [{"name": "News"}, {"stream_id": 1}, {"stream_id": 1, "name": "News", "num": "x"}]
)
def test_channel_rejects_malformed_xtream_live_stream(record: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        XtreamDomainTranslator.channel(record, ProviderId("xtream-demo"))
