"""Explicit, stale-safe playback state transitions for Player 2."""

from __future__ import annotations

from dataclasses import dataclass

from samotech_iptv.application.dtos.player import PlaybackState

__all__ = ["PlaybackStateMachine", "PlaybackStateSnapshot"]


@dataclass(frozen=True)
class PlaybackStateSnapshot:
    """Current state and correlation identity owned by the player service."""

    state: PlaybackState
    media_generation: int
    session_token: int
    reason: str | None = None


_VALID_TRANSITIONS: dict[PlaybackState, frozenset[PlaybackState]] = {
    PlaybackState.IDLE: frozenset(
        {PlaybackState.LOADING, PlaybackState.STOPPING, PlaybackState.STOPPED, PlaybackState.ERROR}
    ),
    PlaybackState.LOADING: frozenset(
        {
            PlaybackState.BUFFERING,
            PlaybackState.PLAYING,
            PlaybackState.STOPPING,
            PlaybackState.STOPPED,
            PlaybackState.RECOVERING,
            PlaybackState.ERROR,
        }
    ),
    PlaybackState.BUFFERING: frozenset(
        {
            PlaybackState.PLAYING,
            PlaybackState.STOPPING,
            PlaybackState.STOPPED,
            PlaybackState.RECOVERING,
            PlaybackState.ERROR,
        }
    ),
    PlaybackState.PLAYING: frozenset(
        {
            PlaybackState.BUFFERING,
            PlaybackState.PAUSED,
            PlaybackState.STOPPING,
            PlaybackState.STOPPED,
            PlaybackState.ENDED,
            PlaybackState.RECOVERING,
            PlaybackState.ERROR,
        }
    ),
    PlaybackState.PAUSED: frozenset(
        {
            PlaybackState.PLAYING,
            PlaybackState.STOPPING,
            PlaybackState.STOPPED,
            PlaybackState.ENDED,
            PlaybackState.ERROR,
        }
    ),
    PlaybackState.STOPPING: frozenset({PlaybackState.STOPPED, PlaybackState.ERROR}),
    PlaybackState.STOPPED: frozenset(
        {PlaybackState.IDLE, PlaybackState.LOADING, PlaybackState.ERROR}
    ),
    PlaybackState.ENDED: frozenset(
        {PlaybackState.IDLE, PlaybackState.LOADING, PlaybackState.STOPPED, PlaybackState.ERROR}
    ),
    PlaybackState.RECOVERING: frozenset(
        {
            PlaybackState.LOADING,
            PlaybackState.BUFFERING,
            PlaybackState.PLAYING,
            PlaybackState.STOPPING,
            PlaybackState.STOPPED,
            PlaybackState.ERROR,
        }
    ),
    PlaybackState.ERROR: frozenset(
        {PlaybackState.IDLE, PlaybackState.LOADING, PlaybackState.STOPPING, PlaybackState.STOPPED}
    ),
}


class PlaybackStateMachine:
    """Apply only valid transitions for the current media/session generation."""

    def __init__(self) -> None:
        self._snapshot = PlaybackStateSnapshot(PlaybackState.IDLE, 0, 0)

    @property
    def snapshot(self) -> PlaybackStateSnapshot:
        """Return an immutable snapshot for UI or diagnostics."""
        return self._snapshot

    def reset_context(
        self,
        *,
        media_generation: int,
        session_token: int,
        state: PlaybackState,
        reason: str | None = None,
    ) -> PlaybackStateSnapshot:
        """Start a new command/session context without accepting stale events."""
        self._snapshot = PlaybackStateSnapshot(state, media_generation, session_token, reason)
        return self._snapshot

    def transition(
        self,
        state: PlaybackState,
        *,
        media_generation: int,
        session_token: int,
        reason: str | None = None,
    ) -> bool:
        """Apply one current-generation transition; reject stale/invalid events harmlessly."""
        current = self._snapshot
        if media_generation != current.media_generation or session_token != current.session_token:
            return False
        if state is current.state:
            self._snapshot = PlaybackStateSnapshot(
                state, media_generation, session_token, reason or current.reason
            )
            return True
        if state not in _VALID_TRANSITIONS[current.state]:
            return False
        self._snapshot = PlaybackStateSnapshot(state, media_generation, session_token, reason)
        return True
