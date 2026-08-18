from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.application.dtos.playback import (
    PlaybackAttempt,
    PlaybackOutcome,
    PlaybackResult,
    PlaybackTarget,
    ResolvedPlayback,
)
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.ports.provider_non_live_resolver_port import (
        ProviderNonLivePlaybackResolverPort,
    )
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
    from samotech_iptv.application.use_cases.record_history import RecordHistory
    from samotech_iptv.domain.repositories.history_repository import HistoryRepository


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
        non_live_provider_resolver: ProviderNonLivePlaybackResolverPort | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._non_live_provider_resolver = non_live_provider_resolver
        self._player = player
        self._record_history = record_history
        self._history_repository = history_repository
        self._attempts = attempts or PlaybackAttemptRegistry()

    @property
    def attempts(self) -> PlaybackAttemptRegistry:
        """Expose the application-owned attempt registry for explicit invalidation."""
        return self._attempts

    async def execute(self, target: PlaybackTarget) -> PlaybackResult:
        """Play the latest supported provider-scoped target through one player path."""
        attempt = self._attempts.begin(target)
        if target.content_type is not ContentType.LIVE and self._non_live_provider_resolver is None:
            return PlaybackResult(attempt, PlaybackOutcome.UNSUPPORTED, "Playback is unavailable")
        try:
            playback, history_item_type = await self._resolve_target(target)
        except Exception:
            if not self._attempts.is_current(attempt):
                return PlaybackResult(attempt, PlaybackOutcome.STALE)
            return PlaybackResult(attempt, PlaybackOutcome.FAILED, "Unable to start playback")
        if not self._attempts.is_current(attempt):
            return PlaybackResult(attempt, PlaybackOutcome.STALE)
        try:
            await self._player.play(playback)
        except Exception:
            if not self._attempts.is_current(attempt):
                return PlaybackResult(attempt, PlaybackOutcome.STALE)
            return PlaybackResult(attempt, PlaybackOutcome.FAILED, "Unable to start playback")
        if not self._attempts.is_current(attempt):
            return PlaybackResult(attempt, PlaybackOutcome.STALE)
        await self._restore_resume_if_safe(target)
        if self._record_history is not None:
            from samotech_iptv.application.dtos import RecordHistoryRequest

            try:
                await self._record_history.execute(
                    RecordHistoryRequest(
                        item_id=target.canonical_content_id,
                        item_type=history_item_type,
                        provider_id=target.provider_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise ProviderError("Unable to record playback history") from exc
        return PlaybackResult(attempt, PlaybackOutcome.PLAYED)

    async def _restore_resume_if_safe(self, target: PlaybackTarget) -> None:
        """Restore only provider-scoped VOD/episode positions that are not completed."""
        if self._history_repository is None or target.content_type is ContentType.LIVE:
            return
        item_type = "movie" if target.content_type is ContentType.MOVIE else "episode"
        try:
            record = await self._history_repository.find_latest(
                provider_id=target.provider_id,
                item_id=target.canonical_content_id,
                item_type=item_type,
            )
            if record is None or record.completed or record.position_seconds <= 0:
                return
            await self._player.seek_ms(record.position_seconds * 1_000)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Resume is an enhancement; a missing native seek must never fail playback.
            return

    async def _resolve_target(self, target: PlaybackTarget) -> tuple[ResolvedPlayback, str]:
        """Resolve exactly one target type at its provider-to-player boundary."""
        if target.content_type is ContentType.LIVE:
            from samotech_iptv.domain.value_objects.channel_id import ChannelId

            provider = self._provider_resolver.resolve_playback_provider(target.provider_id)
            playback = await provider.resolve_stream(ChannelId(target.canonical_content_id))
            return self._attach_resource(playback, target), "channel"
        if target.content_type is ContentType.MOVIE:
            resolver = self._non_live_provider_resolver
            if resolver is None:
                raise ProviderError("Movie playback is unavailable")
            movie_provider = resolver.resolve_movie_playback_provider(target.provider_id)
            playback = await movie_provider.resolve_movie_stream(
                target.canonical_content_id, target.resource_id or ""
            )
            return self._attach_resource(playback, target), "movie"
        if target.content_type is ContentType.EPISODE:
            resolver = self._non_live_provider_resolver
            if resolver is None:
                raise ProviderError("Episode playback is unavailable")
            episode_provider = resolver.resolve_episode_playback_provider(target.provider_id)
            playback = await episode_provider.resolve_episode_stream(
                target.canonical_content_id, target.resource_id or ""
            )
            return self._attach_resource(playback, target), "episode"
        raise ProviderError("Playback target is unsupported")

    @staticmethod
    def _attach_resource(
        playback: ResolvedPlayback | URL, target: PlaybackTarget
    ) -> ResolvedPlayback:
        """Carry safe logical identity without copying URL or credential state."""
        if isinstance(playback, URL):
            return ResolvedPlayback.from_url(playback, resource=target)
        return ResolvedPlayback(
            url=playback.url,
            transport=playback.transport,
            resource=target,
        )
