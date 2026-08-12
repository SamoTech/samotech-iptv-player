"""Play a selected channel through its registered provider's playback capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import RecordHistoryRequest
from samotech_iptv.application.use_cases.play_channel import PlayChannel

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
    from samotech_iptv.application.use_cases.record_history import RecordHistory

__all__ = ["PlayRegisteredChannel"]


class PlayRegisteredChannel:
    """Resolve a registered provider, then play a selected channel through libVLC."""

    def __init__(
        self,
        provider_resolver: ProviderResolverPort,
        player: PlayerPort,
        record_history: RecordHistory | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._player = player
        self._record_history = record_history

    async def execute(self, provider_id: str, channel_id: str) -> None:
        """Resolve only playback capability, then delegate stream resolution to PlayChannel."""
        provider = self._provider_resolver.resolve_playback_provider(provider_id)
        await PlayChannel(provider, self._player).execute(channel_id)
        if self._record_history is not None:
            await self._record_history.execute(
                RecordHistoryRequest(item_id=channel_id, item_type="channel")
            )
