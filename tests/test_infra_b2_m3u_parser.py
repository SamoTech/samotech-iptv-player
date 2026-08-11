"""Focused tests for canonical extended-M3U parsing."""

from __future__ import annotations

import pytest

from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.parsing.m3u_parser import M3UParser, M3UParserError


@pytest.fixture
def parser() -> M3UParser:
    return M3UParser()


@pytest.fixture
def provider_id() -> ProviderId:
    return ProviderId("m3u-demo")


def test_parse_extended_m3u_maps_metadata_and_streams(
    parser: M3UParser, provider_id: ProviderId
) -> None:
    playlist = (
        "#EXTM3U\n"
        '#EXTINF:-1 tvg-id="bbc.news" '
        'tvg-logo="https://assets.example.test/bbc.png" '
        'group-title="News" tvg-chno="101",BBC News HD\n'
        "https://stream.example.test/live/bbc-news.m3u8\n"
        '#EXTINF:-1 tvg-id=movie-one group-title="Movies",Movie One\n'
        "https://stream.example.test/live/movie-one.ts?token=test\n"
    )

    parsed = parser.parse(playlist, provider_id)

    assert len(parsed.channels) == 2
    assert len(parsed.streams) == 2
    first = parsed.channels[0]
    assert first.id.value == "m3u-demo:bbc-news"
    assert first.name == "BBC News HD"
    assert first.category_id == "News"
    assert first.epg_channel_id == "bbc.news"
    assert first.number == 101
    assert str(first.logo_url) == "https://assets.example.test/bbc.png"
    assert str(parsed.stream_for(first).url) == "https://stream.example.test/live/bbc-news.m3u8"
    assert parsed.stream_for(first).container == "m3u8"
    assert parsed.streams[1].container == "ts"


def test_parse_generates_stable_unique_ids_for_duplicate_titles(
    parser: M3UParser, provider_id: ProviderId
) -> None:
    playlist = """#EXTM3U
#EXTINF:-1 group-title="News",Local News
https://stream.example.test/live/local-news-1
#EXTINF:-1 group-title="News",Local News
https://stream.example.test/live/local-news-2
"""

    parsed = parser.parse(playlist, provider_id)

    assert [channel.id.value for channel in parsed.channels] == [
        "m3u-demo:local-news",
        "m3u-demo:local-news-2",
    ]
    assert parsed.streams[0].id == parsed.channels[0].stream_id
    assert parsed.streams[1].id == parsed.channels[1].stream_id


@pytest.mark.parametrize(
    ("playlist", "message"),
    [
        ("", "must start with #EXTM3U"),
        ("#EXTM3U\nhttps://stream.example.test/orphan", "without #EXTINF"),
        ("#EXTM3U\n#EXTINF:-1,Missing stream", "no following stream URL"),
        (
            "#EXTM3U\n#EXTINF:-1,Unsupported stream\nudp://239.0.0.1:1234",
            "invalid stream URL",
        ),
        (
            "#EXTM3U\n#EXTINF:-1 tvg-chno=not-a-number,Invalid number\nhttps://stream.example.test/live",
            "invalid tvg-chno",
        ),
    ],
)
def test_parse_rejects_invalid_playlist_entries(
    parser: M3UParser, provider_id: ProviderId, playlist: str, message: str
) -> None:
    with pytest.raises(M3UParserError, match=message):
        parser.parse(playlist, provider_id)
