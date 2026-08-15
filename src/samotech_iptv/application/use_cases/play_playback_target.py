from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.application.dtos.playback import (
    PlaybackAttempt,
    PlaybackOutcome,
    PlaybackResult,
    PlaybackTarget,
)
from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
    from samotech_iptv.application.use_cases.record_history import RecordHistory

__all__ = ["PlaybackAttemptRegistry", "PlayPlaybackTarget"]


class PlaybackAttemptRegistry:
    """Keep only the latest explicit playback attempt valid for one player session."""

    def __init__(self) -> None:
        self._generation = 0
        self._current: PlaybackAttempt | None = None

    def begin(self, target: PlaybackTarget) -> PlaybackAttempt:
        """Start a new attempt, invalidating all earlier target resolutions."""
        self._generation += 1
        self._current = PlaybackAttempt(self._generation, target)
        return self._current

    def is_current(self, attempt: PlaybackAttempt) -> bool:
        """Return whether an attempt may still mutate player state."""
        return attempt == self._current

    def invalidate(self) -> None:
        """Invalidate the current target when a provider or player context is cleared."""
        self._generation += 1
        self._current = None


class PlayPlaybackTarget:
    """Resolve and play only the latest supported provider-scoped target."""

    def __init__(
        self,
        provider_resolver: ProviderResolverPort,
        player: PlayerPort,
        record_history: RecordHistory | None = None,
        attempts: PlaybackAttemptRegistry | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._player = player
        self._record_history = record_history
        self._attempts = attempts or PlaybackAttemptRegistry()

    @property
    def attempts(self) -> PlaybackAttemptRegistry:
        """Expose the application-owned attempt registry for explicit invalidation."""
        return self._attempts

    async def execute(self, target: PlaybackTarget) -> PlaybackResult:
        """Play the latest Live target or return an explicit safe unsupported result."""
        attempt = self._attempts.begin(target)
        if target.content_type is not ContentType.LIVE:
            return PlaybackResult(attempt, PlaybackOutcome.UNSUPPORTED, "Playback is unavailable")
        try:
            from samotech_iptv.domain.value_objects.channel_id import ChannelId

            provider = self._provider_resolver.resolve_playback_provider(target.provider_id)
            url = await provider.resolve_stream(ChannelId(target.canonical_content_id))
        except Exception:
            if not self._attempts.is_current(attempt):
                return PlaybackResult(attempt, PlaybackOutcome.STALE)
            return PlaybackResult(attempt, PlaybackOutcome.FAILED, "Unable to start playback")
        if not self._attempts.is_current(attempt):
            return PlaybackResult(attempt, PlaybackOutcome.STALE)
        try:
            await self._player.play(url)
        except Exception:
            if not self._attempts.is_current(attempt):
                return PlaybackResult(attempt, PlaybackOutcome.STALE)
            return PlaybackResult(attempt, PlaybackOutcome.FAILED, "Unable to start playback")
        if not self._attempts.is_current(attempt):
            return PlaybackResult(attempt, PlaybackOutcome.STALE)
        if self._record_history is not None:
            from samotech_iptv.application.dtos import RecordHistoryRequest

            try:
                await self._record_history.execute(
                    RecordHistoryRequest(
                        item_id=target.canonical_content_id,
                        item_type="channel",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise ProviderError("Unable to record playback history") from exc
        return PlaybackResult(attempt, PlaybackOutcome.PLAYED)
