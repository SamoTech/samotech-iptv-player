"""Play a selected channel through its registered provider's playback capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.use_cases.play_channel import PlayChannel

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["PlayRegisteredChannel"]


class PlayRegisteredChannel:
    """Resolve a registered provider, then play a selected channel through libVLC."""

    def __init__(self, provider_resolver: ProviderResolverPort, player: PlayerPort) -> None:
        self._provider_resolver = provider_resolver
        self._player = player

    async def execute(self, provider_id: str, channel_id: str) -> None:
        """Resolve only playback capability, then delegate stream resolution to PlayChannel."""
        provider = self._provider_resolver.resolve_playback_provider(provider_id)
        await PlayChannel(provider, self._player).execute(channel_id)
