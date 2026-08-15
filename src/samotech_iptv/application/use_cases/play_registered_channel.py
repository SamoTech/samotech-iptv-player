"""Play a selected channel through its registered provider's playback capability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    PlaybackOutcome,
    PlaybackResult,
    PlaybackTarget,
)
from samotech_iptv.application.use_cases.play_playback_target import PlayPlaybackTarget
from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_non_live_resolver_port import (
        ProviderNonLivePlaybackResolverPort,
    )
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
        non_live_provider_resolver: ProviderNonLivePlaybackResolverPort | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._player = player
        self._record_history = record_history
        self._playback_targets = PlayPlaybackTarget(
            provider_resolver,
            player,
            record_history,
            non_live_provider_resolver=non_live_provider_resolver,
        )

    async def execute(self, provider_id: str, channel_id: str) -> None:
        """Retain the legacy Live entry point through the unified target contract."""
        result = await self.execute_target(PlaybackTarget.live(provider_id, channel_id))
        if result.outcome is PlaybackOutcome.FAILED:
            raise ProviderError(result.error or "Unable to start playback")

    async def execute_target(self, target: PlaybackTarget) -> PlaybackResult:
        """Play a provider-scoped target through the single unified application path."""
        return await self._playback_targets.execute(target)

    def invalidate_pending_playback(self) -> None:
        """Prevent a late stream resolution from mutating a cleared playback context."""
        self._playback_targets.attempts.invalidate()
