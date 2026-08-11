"""Unit tests for MAGStream.get_stream_url."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from providers.base.errors import StreamError
from providers.mag.stream import MAGStream


def _make_stream(cmd: str = "ffmpeg http://cdn.example.com/live/1.m3u8") -> MAGStream:
    conn = AsyncMock()
    conn.get = AsyncMock(return_value={"js": {"cmd": cmd}})
    sess = MagicMock()
    sess.get_headers.return_value = {}
    return MAGStream(conn, sess)


@pytest.mark.asyncio
async def test_get_stream_url_happy_path() -> None:
    stream = _make_stream()
    url = await stream.get_stream_url(1, "live")
    assert url.startswith("http")


@pytest.mark.asyncio
async def test_get_stream_url_raises_on_empty_cmd() -> None:
    stream = _make_stream(cmd="")
    with pytest.raises(StreamError):
        await stream.get_stream_url(1, "live")


@pytest.mark.asyncio
async def test_get_stream_url_raises_on_bad_scheme() -> None:
    stream = _make_stream(cmd="ftp://bad-scheme.com/stream")
    with pytest.raises(StreamError, match="scheme"):
        await stream.get_stream_url(1, "live")
