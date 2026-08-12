"""Tests for capability-aware provider-to-player playback orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.use_cases.play_channel import PlayChannel
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_capabilities import PlaybackProvider
    from samotech_iptv.domain.value_objects.channel_id import ChannelId


class FakeProvider:
    """Deterministic provider playback capability fake."""

    async def resolve_stream(self, _: ChannelId) -> URL:
        return URL("https://example.test/live.m3u8")


class FakePlayer:
    """Deterministic player-port fake."""

    def __init__(self) -> None:
        self.url: URL | None = None

    @property
    def is_playing(self) -> bool:
        return self.url is not None

    async def play(self, url: URL) -> None:
        self.url = url

    async def stop(self) -> None:
        self.url = None

    async def pause(self) -> None:
        return None

    async def resume(self) -> None:
        return None


@pytest.mark.asyncio
async def test_play_channel_resolves_provider_url_then_invokes_player() -> None:
    player = FakePlayer()
    use_case = PlayChannel(cast("PlaybackProvider", FakeProvider()), cast("PlayerPort", player))

    await use_case.execute("xtream-demo:1")

    assert player.url == URL("https://example.test/live.m3u8")
