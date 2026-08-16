from __future__ import annotations

from samotech_iptv.application.dtos.player import PlaybackState
from samotech_iptv.application.player_state_machine import PlaybackStateMachine


def test_state_machine_accepts_valid_transitions_and_duplicate_events() -> None:
    machine = PlaybackStateMachine()
    machine.reset_context(media_generation=1, session_token=1, state=PlaybackState.LOADING)

    assert machine.transition(PlaybackState.BUFFERING, media_generation=1, session_token=1) is True
    assert machine.transition(PlaybackState.BUFFERING, media_generation=1, session_token=1) is True
    assert machine.transition(PlaybackState.PLAYING, media_generation=1, session_token=1) is True
    assert machine.transition(PlaybackState.PAUSED, media_generation=1, session_token=1) is True
    assert machine.transition(PlaybackState.PLAYING, media_generation=1, session_token=1) is True
    assert machine.snapshot.state is PlaybackState.PLAYING


def test_state_machine_rejects_invalid_and_stale_events_without_mutation() -> None:
    machine = PlaybackStateMachine()
    machine.reset_context(media_generation=2, session_token=3, state=PlaybackState.PLAYING)

    assert machine.transition(PlaybackState.ENDED, media_generation=1, session_token=3) is False
    assert machine.snapshot.state is PlaybackState.PLAYING
    assert machine.transition(PlaybackState.IDLE, media_generation=2, session_token=3) is False
    assert machine.snapshot.state is PlaybackState.PLAYING


def test_state_machine_allows_terminal_stop_and_new_generation() -> None:
    machine = PlaybackStateMachine()
    machine.reset_context(media_generation=4, session_token=5, state=PlaybackState.PLAYING)

    assert machine.transition(PlaybackState.STOPPING, media_generation=4, session_token=5) is True
    assert machine.transition(PlaybackState.STOPPED, media_generation=4, session_token=5) is True
    machine.reset_context(media_generation=5, session_token=6, state=PlaybackState.LOADING)
    assert machine.snapshot.media_generation == 5
    assert machine.snapshot.session_token == 6
    assert machine.snapshot.state is PlaybackState.LOADING
