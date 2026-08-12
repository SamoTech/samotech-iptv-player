"""Tests for M3U source loading and capability-oriented provider translation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.parsing.m3u_source_loader import (
    M3USourceError,
    M3USourceLoader,
)
from samotech_iptv.infrastructure.providers.m3u_adapter import M3UProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

if TYPE_CHECKING:
    from pathlib import Path


_PLAYLIST = "#EXTM3U\n#EXTINF:-1 tvg-id=one,One\nhttps://stream.example.test/live/one.m3u8\n"
_RTSP_PLAYLIST = "#EXTM3U\n#EXTINF:-1 tvg-id=rtsp,RTSP\nrtsp://stream.example.test/live\n"


class FakeHttpClient:
    """Minimal remote-source fake that records HTTP playlist retrieval."""

    def __init__(self, text: str = _PLAYLIST) -> None:
        self.text = text
        self.urls: list[str] = []

    async def get_text(self, url: str) -> str:
        self.urls.append(url)
        return self.text


class FakeSourceLoader:
    """Deterministic source-loader fake for adapter contract tests."""

    def __init__(self, text: str = _PLAYLIST) -> None:
        self._text = text

    async def load(self, source: str) -> str:
        assert source == "https://playlist.example.test/list.m3u"
        return self._text


@pytest.mark.asyncio
async def test_source_loader_reads_local_playlist(tmp_path: Path) -> None:
    """A local M3U file is loaded without using the remote HTTP boundary."""
    playlist_path = tmp_path / "channels.m3u"
    playlist_path.write_text(_PLAYLIST, encoding="utf-8")

    loader = M3USourceLoader(FakeHttpClient())  # type: ignore[arg-type]

    assert await loader.load(str(playlist_path)) == _PLAYLIST


@pytest.mark.asyncio
async def test_source_loader_fetches_remote_http_playlist() -> None:
    """A remote HTTP(S) M3U source uses the injected HTTP client boundary."""
    client = FakeHttpClient()
    loader = M3USourceLoader(client)  # type: ignore[arg-type]

    assert await loader.load("https://playlist.example.test/list.m3u") == _PLAYLIST
    assert client.urls == ["https://playlist.example.test/list.m3u"]


@pytest.mark.asyncio
async def test_source_loader_rejects_unsupported_source_scheme() -> None:
    """Unsupported source transports fail through a controlled source error."""
    loader = M3USourceLoader(FakeHttpClient())  # type: ignore[arg-type]

    with pytest.raises(M3USourceError, match="Unsupported M3U source scheme"):
        await loader.load("ftp://playlist.example.test/list.m3u")


@pytest.mark.asyncio
async def test_m3u_adapter_translates_loaded_source_and_declares_capabilities() -> None:
    """The adapter composes M3U source loading with canonical parser translation."""
    metadata = InfraProviderMetadata(
        provider_id="m3u-demo",
        provider_type="m3u",
        base_url="https://playlist.example.test/list.m3u",
    )
    adapter = M3UProviderAdapter(
        metadata,
        ProviderContext.build(overrides={"max_retries": 1}),
        source_loader=FakeSourceLoader(),
    )

    channels = await adapter.load_channels()

    assert adapter.supported_capabilities() == {
        ProviderCapability.LIVE,
        ProviderCapability.SEARCH,
        ProviderCapability.STREAM_RESOLUTION,
    }
    assert [channel.name for channel in channels] == ["One"]
    assert [channel.name for channel in await adapter.search_channels("one")] == ["One"]
    assert await adapter.resolve_stream(channels[0].id) == URL(
        "https://stream.example.test/live/one.m3u8"
    )


@pytest.mark.asyncio
async def test_m3u_adapter_rejects_unknown_or_non_http_playback_urls_safely() -> None:
    """Resolution hides channel and source details when a player-compatible URL is unavailable."""
    metadata = InfraProviderMetadata(
        provider_id="m3u-demo",
        provider_type="m3u",
        base_url="https://playlist.example.test/list.m3u",
    )
    adapter = M3UProviderAdapter(
        metadata,
        ProviderContext.build(overrides={"max_retries": 1}),
        source_loader=FakeSourceLoader(_RTSP_PLAYLIST),
    )
    channels = await adapter.load_channels()

    with pytest.raises(ProviderError, match="supported playback URL") as unsupported_error:
        await adapter.resolve_stream(channels[0].id)
    with pytest.raises(ProviderError, match="was not found") as unknown_error:
        await adapter.resolve_stream(type(channels[0].id)("m3u-demo:unknown"))

    assert "rtsp" not in str(unsupported_error.value)
    assert "unknown" not in str(unknown_error.value)
