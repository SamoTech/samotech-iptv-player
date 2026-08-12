from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.ports.player_port import PlayerPort
from samotech_iptv.application.ports.provider_capabilities import PlaybackProvider
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.application.use_cases.play_registered_channel import PlayRegisteredChannel
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.channel_id import ChannelId


class FakePlaybackProvider(PlaybackProvider):
    """Playback-capable provider double recording the selected channel identifier."""

    def __init__(self) -> None:
        self.channel_ids: list[str] = []

    async def resolve_stream(self, channel_id: ChannelId) -> URL:
        self.channel_ids.append(channel_id.value)
        return URL("https://example.invalid/live.m3u8")


class FakeResolver(ProviderResolverPort):
    """Resolver double exposing only the requested provider's playback capability."""

    def __init__(self, provider: PlaybackProvider) -> None:
        self._provider = provider
        self.provider_ids: list[str] = []

    def resolve_catalog_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected catalogue resolution for {provider_id}")

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        self.provider_ids.append(provider_id)
        return self._provider


class FakePlayer(PlayerPort):
    """Player-port double retaining the resolved playback URL."""

    def __init__(self) -> None:
        self.urls: list[URL] = []

    async def play(self, url: URL) -> None:
        self.urls.append(url)

    async def stop(self) -> None:
        return None

    async def pause(self) -> None:
        return None

    async def resume(self) -> None:
        return None

    def attach_video_output(self, native_window_id: int) -> None:
        return None

    @property
    def is_playing(self) -> bool:
        return bool(self.urls)


@pytest.mark.asyncio
async def test_play_registered_channel_resolves_selected_provider_then_plays_channel() -> None:
    provider = FakePlaybackProvider()
    resolver = FakeResolver(provider)
    player = FakePlayer()

    await PlayRegisteredChannel(resolver, player).execute("m3u-demo", "channel-1")

    assert resolver.provider_ids == ["m3u-demo"]
    assert provider.channel_ids == ["channel-1"]
    assert player.urls == [URL("https://example.invalid/live.m3u8")]
