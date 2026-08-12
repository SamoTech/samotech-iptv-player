"""Integration coverage for M3U registered-provider playback resolution."""

from __future__ import annotations

import pytest

from samotech_iptv.application.use_cases.play_registered_channel import PlayRegisteredChannel
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.m3u_adapter import M3UProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)

_PLAYLIST = "#EXTM3U\n#EXTINF:-1 tvg-id=one,One\nhttps://stream.example.test/live/one.m3u8\n"


class FakeSourceLoader:
    """Deterministic M3U source loader used without external provider access."""

    async def load(self, _: str) -> str:
        return _PLAYLIST


class FakePlayer:
    """Minimal player double retaining only the canonical URL passed by the use case."""

    def __init__(self) -> None:
        self.urls: list[URL] = []

    async def play(self, url: URL) -> None:
        self.urls.append(url)


@pytest.mark.asyncio
async def test_registered_m3u_channel_resolves_and_plays_its_parsed_http_stream() -> None:
    """A registered M3U profile completes the resolver-to-player live-TV path."""
    metadata = InfraProviderMetadata(
        provider_id="m3u-demo",
        provider_type="m3u",
        base_url="https://playlist.example.test/list.m3u",
    )
    context = ProviderContext.build(overrides={"max_retries": 1})
    adapter = M3UProviderAdapter(metadata, context, source_loader=FakeSourceLoader())
    registry = ProviderRegistry()
    registry.register(metadata)
    factory = ProviderFactory()
    factory.register_type("m3u", lambda _, **__: adapter)
    resolver = ProviderResolutionService(registry, factory, context)
    player = FakePlayer()
    channel = (await adapter.load_channels())[0]

    await PlayRegisteredChannel(  # type: ignore[arg-type]
        resolver,
        player,
    ).execute(metadata.provider_id, channel.id.value)

    assert player.urls == [URL("https://stream.example.test/live/one.m3u8")]
