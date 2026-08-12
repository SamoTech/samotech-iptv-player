"""Capability-aware provider-to-player playback use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_capabilities import PlaybackProvider

__all__ = ["PlayChannel"]

_LOG = get_logger(__name__)


class PlayChannel:
    """Resolve an authorized provider stream then pass it to the sole player port."""

    def __init__(self, provider: PlaybackProvider, player: PlayerPort) -> None:
        self._provider = provider
        self._player = player

    async def execute(self, channel_id: str) -> None:
        """Resolve and play one channel without leaking provider state into the player."""
        from samotech_iptv.domain.value_objects.channel_id import ChannelId

        _LOG.info("Resolving and playing channel %s", channel_id)
        url = await self._provider.resolve_stream(ChannelId(channel_id))
        await self._player.play(url)
