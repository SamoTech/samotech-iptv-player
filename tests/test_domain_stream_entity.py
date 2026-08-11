"""Tests for Stream playback-metadata domain invariants."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.stream import Stream
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL


def _stream(
    *,
    container: str = "m3u8",
    codec: str | None = "h264",
    bitrate_kbps: int | None = 4500,
    is_encrypted: bool = False,
) -> Stream:
    return Stream(
        id=StreamId("stream-1"),
        url=URL("https://stream.example.test/live/1.m3u8"),
        container=container,
        codec=codec,
        bitrate_kbps=bitrate_kbps,
        is_encrypted=is_encrypted,
    )


def test_stream_accepts_complete_playback_metadata() -> None:
    stream = _stream(is_encrypted=True)

    assert stream.container == "m3u8"
    assert stream.codec == "h264"
    assert stream.bitrate_kbps == 4500
    assert stream.is_encrypted is True


def test_stream_is_value_equal_and_hashable() -> None:
    first = _stream()
    second = _stream()

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    ("container", "codec", "bitrate_kbps", "message"),
    [
        (" ", "h264", 4500, "Stream container"),
        ("m3u8", " ", 4500, "Stream codec"),
        ("m3u8", "h264", 0, "Stream bitrate"),
        ("m3u8", "h264", -1, "Stream bitrate"),
    ],
)
def test_stream_rejects_invalid_playback_metadata(
    container: str,
    codec: str,
    bitrate_kbps: int,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _stream(
            container=container,
            codec=codec,
            bitrate_kbps=bitrate_kbps,
        )


def test_stream_allows_unspecified_codec_and_bitrate() -> None:
    stream = _stream(codec=None, bitrate_kbps=None)

    assert stream.codec is None
    assert stream.bitrate_kbps is None
