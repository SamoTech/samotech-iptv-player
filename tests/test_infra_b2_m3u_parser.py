"""Focused tests for canonical extended-M3U parsing."""

from __future__ import annotations

import pytest

from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_protocol import StreamTransport
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


def test_parse_ignores_invalid_optional_logo_url(
    parser: M3UParser, provider_id: ProviderId
) -> None:
    """A malformed optional logo must not discard an otherwise valid channel."""
    parsed = parser.parse(
        '#EXTM3U\n#EXTINF:-1 tvg-logo="not-a-url",Test Channel\n'
        "https://stream.example.test/live/test.ts\n",
        provider_id,
    )

    assert len(parsed.channels) == 1
    assert parsed.channels[0].logo_url is None


def test_parse_preserves_title_and_category_when_quoted_attribute_contains_comma(
    parser: M3UParser, provider_id: ProviderId
) -> None:
    """Quoted HTTP header metadata must not be mistaken for the EXTINF title separator."""
    parsed = parser.parse(
        "#EXTM3U\n"
        '#EXTINF:-1 tvg-id="public.demo" '
        'http-user-agent="Mozilla/5.0 (X11, Linux x86_64)" '
        'group-title="News",Public Demo\n'
        "https://stream.example.test/live/public-demo.m3u8\n",
        provider_id,
    )

    assert len(parsed.channels) == 1
    assert parsed.channels[0].name == "Public Demo"
    assert parsed.channels[0].category_id == "News"
    assert parsed.channels[0].epg_channel_id == "public.demo"


def test_parse_preserves_supported_udp_streams(parser: M3UParser, provider_id: ProviderId) -> None:
    """M3U content entries can carry supported non-HTTP media transports."""
    parsed = parser.parse(
        "#EXTM3U\n#EXTINF:-1,Multicast News\nudp://239.0.0.1:1234\n",
        provider_id,
    )

    assert str(parsed.streams[0].url) == "udp://239.0.0.1:1234"
    assert parsed.streams[0].transport is StreamTransport.UDP


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
            "#EXTM3U\n#EXTINF:-1,Unsupported stream\nftp://stream.example.test/live",
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
