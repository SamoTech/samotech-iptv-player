from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos.playback import (
    PlaybackOutcome,
    PlaybackResource,
    PlaybackTarget,
    ResolvedPlayback,
)
from samotech_iptv.application.dtos.player import PlaybackState
from samotech_iptv.application.use_cases.play_playback_target import PlayPlaybackTarget
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter


@dataclass
class FakeMedia:
    """Deterministic libVLC media double retaining stream-output options."""

    url: str
    options: list[str] = field(default_factory=list)

    def add_option(self, option: str) -> None:
        self.options.append(option)

    def slaves_clear(self) -> None:
        self.options.append("slaves-clear")


class FakePlayer:
    """Deterministic libVLC player double."""

    def __init__(self) -> None:
        self.media: FakeMedia | None = None
        self.playing = False
        self.media_time_ms = 0
        self.calls: list[str] = []
        self.audio_descriptions: object = [(1, "English"), (2, b"Commentary")]
        self.audio_active = 1
        self.audio_selected: list[int] = []
        self.subtitle_descriptions: object = [(3, "English CC"), (4, "Deutsch")]
        self.subtitle_active = 4
        self.subtitle_selected: list[int] = []
        self.aspect_ratio: str | None = None
        self.slaves: list[tuple[object, str, bool]] = []
        self.subtitle_delay_us = 0

    def is_playing(self) -> int:
        return int(self.playing)

    def set_media(self, media: FakeMedia) -> None:
        self.media = media

    def play(self) -> int:
        self.calls.append("play")
        self.playing = True
        return 0

    def stop(self) -> None:
        self.calls.append("stop")
        self.playing = False

    def pause(self) -> None:
        self.calls.append("pause")
        self.playing = False

    def get_time(self) -> int:
        return self.media_time_ms

    def audio_get_track_description(self) -> object:
        return self.audio_descriptions

    def audio_get_track(self) -> int:
        return self.audio_active

    def audio_set_track(self, track_id: int) -> int:
        self.audio_selected.append(track_id)
        self.audio_active = track_id
        return 0

    def video_get_spu_description(self) -> object:
        return self.subtitle_descriptions

    def video_get_spu(self) -> int:
        return self.subtitle_active

    def video_set_spu(self, track_id: int) -> int:
        self.subtitle_selected.append(track_id)
        self.subtitle_active = track_id
        return 0

    def add_slave(self, slave_type: object, uri: str, select: bool) -> int:
        self.slaves.append((slave_type, uri, select))
        return 0

    def video_get_spu_delay(self) -> int:
        return self.subtitle_delay_us

    def video_set_spu_delay(self, delay_us: int) -> int:
        self.subtitle_delay_us = delay_us
        return 0

    def video_get_aspect_ratio(self) -> str | None:
        return self.aspect_ratio

    def video_set_aspect_ratio(self, aspect_ratio: str | None) -> int:
        self.aspect_ratio = aspect_ratio
        return 0

    def set_xwindow(self, native_window_id: int) -> None:
        self.calls.append(f"xwindow:{native_window_id}")

    def set_hwnd(self, native_window_id: int) -> None:
        self.calls.append(f"hwnd:{native_window_id}")

    def set_nsobject(self, native_window_id: int) -> None:
        self.calls.append(f"nsobject:{native_window_id}")

    def release(self) -> None:
        self.calls.append("release")


class FakeEventManager:
    """Deterministic libVLC event manager retaining callback registrations."""

    def __init__(self) -> None:
        self.attachments: list[tuple[object, object]] = []

    def event_attach(self, event_type: object, callback: object) -> None:
        self.attachments.append((event_type, callback))

    def event_detach(self, event_type: object) -> None:
        self.attachments = [
            (attached_type, callback)
            for attached_type, callback in self.attachments
            if attached_type is not event_type
        ]

    def emit(self, event_type: object) -> None:
        for attached_type, callback in self.attachments:
            if attached_type is event_type:
                callback(object())  # type: ignore[operator]


class EventPlayer(FakePlayer):
    """Fake player exposing the six libVLC lifecycle subscriptions."""

    def __init__(self) -> None:
        super().__init__()
        self.events = FakeEventManager()

    def event_manager(self) -> FakeEventManager:
        return self.events


class FailingOncePlayer(FakePlayer):
    def __init__(self) -> None:
        super().__init__()
        self._play_attempts = 0

    def play(self) -> int:
        self._play_attempts += 1
        self.calls.append("play")
        if self._play_attempts == 1:
            return -1
        self.playing = True
        return 0


class RecoveryFailingPlayer(EventPlayer):
    """Starts initially, then rejects every adapter-managed recovery restart."""

    def __init__(self) -> None:
        super().__init__()
        self._play_attempts = 0

    def play(self) -> int:
        self._play_attempts += 1
        self.calls.append("play")
        if self._play_attempts > 1:
            return -1
        self.playing = True
        return 0


class FakeInstance:
    """Deterministic libVLC instance double."""

    def __init__(self, player: FakePlayer) -> None:
        self.player = player
        self.release_calls = 0

    def media_player_new(self) -> FakePlayer:
        return self.player

    def media_new(self, url: str) -> FakeMedia:
        return FakeMedia(url)

    def release(self) -> None:
        self.release_calls += 1


def _adapter(player: FakePlayer, **kwargs: object) -> VlcPlayerAdapter:
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: FakeInstance(player)))
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    return module.VlcPlayerAdapter(FakeInstance(player), player, **kwargs)


def _event_adapter(
    monkeypatch: pytest.MonkeyPatch,
    player: EventPlayer,
    **kwargs: object,
) -> tuple[VlcPlayerAdapter, SimpleNamespace]:
    """Build one event-capable adapter with deterministic lifecycle event tokens."""
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    event_types = SimpleNamespace(
        MediaPlayerOpening=object(),
        MediaPlayerBuffering=object(),
        MediaPlayerPlaying=object(),
        MediaPlayerEncounteredError=object(),
        MediaPlayerEndReached=object(),
        MediaPlayerStopped=object(),
    )
    monkeypatch.setattr(module.vlc, "EventType", event_types, raising=False)
    return module.VlcPlayerAdapter(FakeInstance(player), player, **kwargs), event_types


async def _flush_asyncio(turns: int = 12) -> None:
    """Advance scheduled native-event and zero-delay recovery tasks deterministically."""
    await asyncio.sleep(0.02)
    for _ in range(turns):
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_vlc_adapter_controls_libvlc_playback() -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    assert adapter.state is PlaybackState.IDLE
    assert adapter.capabilities.explicit_state is True
    assert adapter.capabilities.current_position is True
    assert adapter.capabilities.duration is True
    assert adapter.capabilities.absolute_seek is True
    assert adapter.capabilities.volume is True
    assert adapter.capabilities.mute is True

    await adapter.play(URL("https://example.test/live.m3u8"))
    assert adapter.is_playing is True
    assert adapter.state is PlaybackState.LOADING
    assert player.media is not None
    assert player.media.url == "https://example.test/live.m3u8"
    assert player.media.options == [":network-caching=1000"]

    await adapter.pause()
    assert adapter.is_playing is False
    assert adapter.state is PlaybackState.PAUSED
    await adapter.resume()
    assert adapter.state is PlaybackState.LOADING
    await adapter.stop()
    assert adapter.state is PlaybackState.STOPPED

    assert player.calls == ["play", "pause", "play", "stop"]


@pytest.mark.asyncio
async def test_vlc_adapter_enumerates_and_selects_native_tracks_safely() -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    audio_tracks = await adapter.get_audio_tracks()
    subtitle_tracks = await adapter.get_subtitle_tracks()

    assert [(track.id, track.description, track.active) for track in audio_tracks] == [
        (1, "English", True),
        (2, "Commentary", False),
    ]
    assert [(track.id, track.description, track.active) for track in subtitle_tracks] == [
        (3, "English CC", False),
        (4, "Deutsch", True),
    ]
    assert adapter.capabilities.audio_tracks is True
    assert adapter.capabilities.subtitle_tracks is True

    await adapter.select_audio_track(2)
    await adapter.select_subtitle_track(3)
    await adapter.select_subtitle_track(None)
    assert player.audio_selected == [2]
    assert player.subtitle_selected == [3, -1]

    with pytest.raises(ValueError, match="audio track is unavailable"):
        await adapter.select_audio_track(99)
    with pytest.raises(ValueError, match="subtitle track is unavailable"):
        await adapter.select_subtitle_track(99)


@pytest.mark.asyncio
async def test_vlc_adapter_restarts_current_media_and_controls_aspect_ratio() -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    await adapter.play(URL("https://example.test/movie.mp4"))
    await adapter.set_aspect_ratio("16:9")
    assert await adapter.get_aspect_ratio() == "16:9"
    await adapter.restart()
    assert player.calls == ["play", "stop", "play"]

    with pytest.raises(ValueError, match="unsupported aspect ratio"):
        await adapter.set_aspect_ratio("not-a-ratio")


@pytest.mark.asyncio
async def test_vlc_adapter_skips_malformed_track_metadata() -> None:
    player = FakePlayer()
    player.audio_descriptions = [("bad", "ignored"), (5,), (6, None), (7, b" "), (8, "Valid")]
    player.subtitle_descriptions = object()
    adapter = _adapter(player)

    assert [track.id for track in await adapter.get_audio_tracks()] == [6, 7, 8]
    assert [track.description for track in await adapter.get_audio_tracks()] == [
        None,
        None,
        "Valid",
    ]
    assert await adapter.get_subtitle_tracks() == ()


@pytest.mark.asyncio
async def test_vlc_adapter_stops_previous_media_and_falls_back_once() -> None:
    player = FailingOncePlayer()
    adapter = _adapter(player, playback_mode="auto", play_retry_count=1)

    await adapter.play(URL("https://example.test/first.m3u8"))
    assert player.media is not None
    assert player.media.options == [":network-caching=1000", ":avcodec-hw=none"]

    await adapter.play(URL("https://example.test/second.m3u8"))

    assert player.calls == ["play", "stop", "play", "stop", "play"]
    assert player.media is not None
    assert player.media.url == "https://example.test/second.m3u8"
    assert player.media.options == [":network-caching=1000"]


@pytest.mark.asyncio
async def test_vlc_adapter_serializes_rapid_switching_and_stop() -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    first = URL("https://example.test/first.m3u8")
    second = URL("https://example.test/second.m3u8")
    third = URL("https://example.test/third.m3u8")

    await asyncio.gather(adapter.play(first), adapter.play(second), adapter.play(third))

    assert player.calls == ["play", "stop", "play", "stop", "play"]
    assert player.media is not None
    assert player.media.url == third.value

    await asyncio.gather(adapter.play(first), adapter.stop())

    assert player.calls[-3:] == ["stop", "play", "stop"]
    assert adapter.is_playing is False


@pytest.mark.asyncio
async def test_vlc_adapter_releases_player_and_instance_once_on_shutdown() -> None:
    player = FakePlayer()
    instance = FakeInstance(player)
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: instance))
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    adapter = module.VlcPlayerAdapter(instance, player)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.close()
    await adapter.close()

    assert player.calls == ["play", "stop", "release"]
    assert instance.release_calls == 1
    assert adapter.is_playing is False


@pytest.mark.asyncio
async def test_vlc_adapter_rejects_invalid_playback_strategy() -> None:
    player = FakePlayer()
    with pytest.raises(ValueError, match="playback_mode"):
        _adapter(player, playback_mode="invalid")


@pytest.mark.asyncio
async def test_vlc_adapter_records_active_stream_with_duplicate_file_output(tmp_path: Path) -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    destination = tmp_path / "recording.ts"

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.start_recording(destination)

    assert adapter.is_recording is True
    assert player.media is not None
    assert player.media.url == "https://example.test/live.m3u8"
    escaped_destination = str(destination).replace("\\", "\\\\").replace("'", "\\'")
    assert player.media.options == [
        f":sout=#duplicate{{dst=display,dst=std{{access=file,mux=ts,dst='{escaped_destination}'}}}}"
    ]
    assert player.calls == ["play", "stop", "play"]

    await adapter.stop_recording()

    assert adapter.is_recording is False
    assert player.media is not None
    assert player.media.url == "https://example.test/live.m3u8"
    assert player.media.options == [":network-caching=1000"]
    assert player.calls == ["play", "stop", "play", "stop", "play"]


@pytest.mark.asyncio
async def test_vlc_adapter_rejects_invalid_recording_state_or_destination(tmp_path: Path) -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    with pytest.raises(RuntimeError, match="active playback"):
        await adapter.start_recording(tmp_path / "recording.ts")

    await adapter.play(URL("https://example.test/live.m3u8"))
    with pytest.raises(ValueError, match=".ts extension"):
        await adapter.start_recording(tmp_path / "recording.mkv")

    await adapter.start_recording(tmp_path / "recording.ts")
    with pytest.raises(RuntimeError, match="already active"):
        await adapter.start_recording(tmp_path / "second.ts")


@pytest.mark.asyncio
async def test_vlc_adapter_clears_recording_state_when_playback_stops(tmp_path: Path) -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.start_recording(tmp_path / "recording.ts")
    await adapter.stop()

    assert adapter.is_recording is False
    with pytest.raises(RuntimeError, match="No active recording"):
        await adapter.stop_recording()


@pytest.mark.asyncio
async def test_vlc_adapter_emits_safe_stable_correlation_diagnostics(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caplog.set_level(logging.INFO)
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player)

    assert len(player.events.attachments) == 6
    await adapter.play(URL("https://user:secret@example.test/live.m3u8?token=private-value"))
    player.events.emit(event_types.MediaPlayerBuffering)
    player.events.emit(event_types.MediaPlayerBuffering)
    player.events.emit(event_types.MediaPlayerEndReached)
    await adapter.play(URL("https://example.test/second.m3u8"))

    assert len(player.events.attachments) == 6
    messages = [
        record.getMessage()
        for record in caplog.records
        if "PLAYBACK_DIAGNOSTIC" in record.getMessage()
    ]
    joined = "\n".join(messages)
    assert "CONSTRUCT" in joined
    assert "instance_args=none" in joined
    assert "event_subscriptions=6" in joined
    assert "MEDIA" in joined
    assert "media_generation=1" in joined
    assert "media_generation=2" in joined
    assert "event_sequence=1" in joined
    assert "event_sequence=2" in joined
    assert "event_sequence=3" in joined
    assert "event=BUFFERING" in joined
    assert "event=END" in joined
    assert "cause=initial_start" in joined
    assert "cause=channel_switch" in joined
    assert "thread_id=" in joined
    assert "thread_name=" in joined
    assert "https://" not in joined
    assert "example.test" not in joined
    assert "secret" not in joined
    assert "token" not in joined
    assert "private-value" not in joined


@pytest.mark.asyncio
async def test_vlc_adapter_correlation_diagnostics_assign_failure_stop_and_shutdown_causes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    player = FailingOncePlayer()
    adapter = _adapter(player, playback_mode="auto", play_retry_count=1)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.stop()
    await adapter.close()

    messages = [
        record.getMessage()
        for record in caplog.records
        if "PLAYBACK_DIAGNOSTIC" in record.getMessage()
    ]
    joined = "\n".join(messages)
    assert "cause=immediate_play_failure" in joined
    assert "cause=explicit_stop" in joined
    assert "action=release cause=shutdown target=player" in joined
    assert "action=release cause=shutdown target=instance" in joined
    assert "RELEASED" in joined
    assert "last_command_cause=shutdown" in joined


def test_vlc_adapter_attaches_linux_video_output(monkeypatch: pytest.MonkeyPatch) -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    monkeypatch.setattr(
        "samotech_iptv.infrastructure.player.vlc_player_adapter.sys.platform", "linux"
    )

    adapter.attach_video_output(1234)

    assert player.calls == ["xwindow:1234"]


@pytest.mark.asyncio
async def test_native_events_update_public_state_for_current_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_recovery_initial_delay_s=60,
        live_recovery_stability_s=60,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()
    assert adapter.state is PlaybackState.PLAYING

    player.events.emit(event_types.MediaPlayerBuffering)
    await _flush_asyncio()
    assert adapter.state is PlaybackState.BUFFERING

    await adapter.close()


@pytest.mark.asyncio
async def test_live_stall_triggers_liveness_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_stall_timeout_s=0.05,
        live_recovery_initial_delay_s=0,
        live_recovery_stability_s=60,
    )
    playback = ResolvedPlayback(
        URL("https://example.test/live.m3u8"),
        resource=PlaybackResource.live("provider", "channel"),
    )

    await adapter.play(playback)
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()
    await asyncio.sleep(0.12)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    assert adapter._media_generation == 2
    await adapter.close()


@pytest.mark.asyncio
async def test_live_position_advancement_prevents_stall_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_stall_timeout_s=0.15,
        live_recovery_initial_delay_s=0,
        live_recovery_stability_s=60,
    )
    playback = ResolvedPlayback(
        URL("https://example.test/live.m3u8"),
        resource=PlaybackResource.live("provider", "channel"),
    )

    await adapter.play(playback)
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()
    await asyncio.sleep(0.08)
    player.media_time_ms = 1_000
    await asyncio.sleep(0.08)
    await _flush_asyncio()

    assert player.calls == ["play"]
    await adapter.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resource",
    [
        PlaybackResource.movie("provider", "movie", "resource"),
        PlaybackResource.episode(
            "provider",
            "episode",
            "resource",
            "series",
            1,
            1,
        ),
    ],
)
async def test_non_live_end_reaches_normal_completion_without_recovery(
    monkeypatch: pytest.MonkeyPatch,
    resource: PlaybackResource,
) -> None:
    player = EventPlayer()
    adapter, _ = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)
    playback = ResolvedPlayback(URL("https://example.test/vod.mp4"), resource=resource)

    await adapter.play(playback)
    await adapter._handle_native_event("PLAYING", adapter._media_generation, adapter._session_token)
    await adapter._handle_native_event("END", adapter._media_generation, adapter._session_token)
    await _flush_asyncio()

    assert player.calls == ["play"]
    assert adapter.state is PlaybackState.ENDED
    await adapter.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event_name", "expected_state"),
    [("STOPPED", PlaybackState.STOPPED), ("ERROR", PlaybackState.ERROR)],
)
async def test_non_live_failure_events_do_not_trigger_recovery(
    monkeypatch: pytest.MonkeyPatch,
    event_name: str,
    expected_state: PlaybackState,
) -> None:
    player = EventPlayer()
    adapter, _ = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)
    playback = ResolvedPlayback(
        URL("https://example.test/vod.mp4"),
        resource=PlaybackResource.movie("provider", "movie", "resource"),
    )

    await adapter.play(playback)
    await adapter._handle_native_event("PLAYING", adapter._media_generation, adapter._session_token)
    await adapter._handle_native_event(
        event_name, adapter._media_generation, adapter._session_token
    )
    await _flush_asyncio()

    assert player.calls == ["play"]
    assert adapter.state is expected_state
    await adapter.close()


@pytest.mark.asyncio
async def test_liveness_task_cancelled_on_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_stall_timeout_s=60,
        live_recovery_stability_s=60,
    )
    playback = ResolvedPlayback(
        URL("https://example.test/live.m3u8"),
        resource=PlaybackResource.live("provider", "channel"),
    )

    await adapter.play(playback)
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()
    assert adapter._liveness_task is not None

    await adapter.stop()

    assert adapter._liveness_task is None
    assert player.calls == ["play", "stop"]
    await adapter.close()


@pytest.mark.asyncio
async def test_liveness_task_cancelled_on_channel_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_stall_timeout_s=60,
        live_recovery_stability_s=60,
    )
    first = ResolvedPlayback(
        URL("https://example.test/first.m3u8"),
        resource=PlaybackResource.live("provider", "first"),
    )
    second = ResolvedPlayback(
        URL("https://example.test/second.m3u8"),
        resource=PlaybackResource.live("provider", "second"),
    )

    await adapter.play(first)
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()
    assert adapter._liveness_task is not None

    await adapter.play(second)

    assert adapter._liveness_task is None
    assert player.media is not None
    assert player.media.url == second.url.value
    await adapter.close()


@pytest.mark.asyncio
async def test_unexpected_eof_rebuilds_live_media_once(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_recovery_initial_delay_s=0,
        live_recovery_stability_s=60,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    assert adapter._media_generation == 2
    await adapter.close()


@pytest.mark.asyncio
async def test_encountered_error_rebuilds_current_live_media_once(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caplog.set_level(logging.INFO)
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEncounteredError)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    assert adapter.state is PlaybackState.LOADING
    diagnostic_messages = "\n".join(
        record.getMessage()
        for record in caplog.records
        if "PLAYBACK_DIAGNOSTIC" in record.getMessage()
    )
    recovery_messages = "\n".join(
        record.getMessage()
        for record in caplog.records
        if "PLAYBACK_RECOVERY" in record.getMessage()
    )
    assert "to_state=RECOVERING" in diagnostic_messages
    assert "reason=ENCOUNTERED_ERROR" in diagnostic_messages
    assert "error_classification=ENCOUNTERED_ERROR" in diagnostic_messages
    assert "transport_type=https" in diagnostic_messages
    assert "attempt=1" in recovery_messages
    assert "transport_type=https" in recovery_messages
    assert "https://" not in diagnostic_messages
    assert "https://" not in recovery_messages
    await adapter.close()


@pytest.mark.asyncio
async def test_stale_encountered_error_from_previous_generation_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, _ = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/first.m3u8"))
    prior_generation = adapter._media_generation
    prior_session = adapter._session_token
    await adapter.play(URL("https://example.test/second.m3u8"))
    await adapter._handle_native_event("ERROR", prior_generation, prior_session)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_repeated_encountered_errors_schedule_one_recovery_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEncounteredError)
    player.events.emit(event_types.MediaPlayerEncounteredError)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_encountered_error_recovery_honors_attempt_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = RecoveryFailingPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_recovery_max_attempts=1,
        live_recovery_initial_delay_s=0,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEncounteredError)
    await _flush_asyncio(20)

    assert player.calls == ["play", "stop", "play"]
    assert adapter.state is PlaybackState.ERROR
    await adapter.close()


@pytest.mark.asyncio
async def test_unexpected_stopped_rebuilds_live_media_once(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerStopped)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_explicit_stop_does_not_trigger_live_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.stop()
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio()

    assert player.calls == ["play", "stop"]
    assert adapter._state.name == "STOPPED"
    await adapter.close()


@pytest.mark.asyncio
async def test_application_shutdown_does_not_trigger_live_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.close()
    player.events.emit(event_types.MediaPlayerStopped)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "release"]
    assert player.events.attachments == []


@pytest.mark.asyncio
async def test_channel_switch_invalidates_pending_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=1)
    first = URL("https://example.test/first.m3u8")
    second = URL("https://example.test/second.m3u8")

    await adapter.play(first)
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio(2)
    await adapter.play(second)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    assert player.media is not None
    assert player.media.url == second.value
    await adapter.close()


@pytest.mark.asyncio
async def test_stale_eof_from_previous_generation_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, _ = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/first.m3u8"))
    prior_generation = adapter._media_generation
    prior_session = adapter._session_token
    await adapter.play(URL("https://example.test/second.m3u8"))
    await adapter._handle_native_event("END", prior_generation, prior_session)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_buffering_alone_does_not_restart_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_buffering_timeout_s=60)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerBuffering)
    await _flush_asyncio()

    assert player.calls == ["play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_prolonged_buffering_rebuilds_live_media(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_buffering_timeout_s=0,
        live_recovery_initial_delay_s=0,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerBuffering)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


def test_live_recovery_uses_bounded_exponential_backoff() -> None:
    adapter = _adapter(
        FakePlayer(),
        live_recovery_initial_delay_s=1,
        live_recovery_max_delay_s=8,
    )

    assert [adapter._recovery_delay_s(attempt) for attempt in range(1, 7)] == [1, 2, 4, 8, 8, 8]


@pytest.mark.asyncio
async def test_concurrent_eof_and_buffering_schedule_one_recovery_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerBuffering)
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_recovery_budget_resets_only_after_stability_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_recovery_initial_delay_s=0,
        live_recovery_stability_s=0,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio()
    assert adapter._recovery_attempts == 1
    player.events.emit(event_types.MediaPlayerPlaying)
    await _flush_asyncio()

    assert adapter._recovery_attempts == 0
    await adapter.close()


@pytest.mark.asyncio
async def test_recovery_stops_after_configured_attempt_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = RecoveryFailingPlayer()
    adapter, event_types = _event_adapter(
        monkeypatch,
        player,
        live_recovery_max_attempts=1,
        live_recovery_initial_delay_s=0,
    )

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio(20)

    assert player.calls == ["play", "stop", "play"]
    assert adapter._state.name == "FAILED"
    await adapter.close()


@pytest.mark.asyncio
async def test_paused_playback_does_not_treat_native_end_as_live_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.pause()
    player.events.emit(event_types.MediaPlayerEndReached)
    await _flush_asyncio()

    assert player.calls == ["play", "pause"]
    await adapter.close()


@pytest.mark.asyncio
async def test_recording_restart_does_not_trigger_live_recovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    player = EventPlayer()
    adapter, _ = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    await adapter.start_recording(tmp_path / "recording.ts")
    await adapter._handle_native_event("END", adapter._media_generation, adapter._session_token)
    await _flush_asyncio()

    assert player.calls == ["play", "stop", "play"]
    await adapter.close()


@pytest.mark.asyncio
async def test_non_live_target_never_reaches_vlc_adapter() -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    use_case = PlayPlaybackTarget(object(), adapter)

    result = await use_case.execute(PlaybackTarget.movie("provider", "movie", "resource"))

    assert result.outcome is PlaybackOutcome.UNSUPPORTED
    assert player.calls == []
    await adapter.close()


@pytest.mark.asyncio
async def test_immediate_initial_play_failure_behavior_is_preserved() -> None:
    player = FailingOncePlayer()
    adapter = _adapter(player, playback_mode="auto", play_retry_count=1)

    await adapter.play(URL("https://example.test/live.m3u8"))

    assert player.calls == ["play", "stop", "play"]
    assert adapter._media_generation == 2
    await adapter.close()


@pytest.mark.asyncio
async def test_vlc_media_options_preserve_multiple_headers_and_special_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    from samotech_iptv.application.dtos.playback import (
        PlaybackResource,
        ResolvedPlayback,
        TransportHeader,
        TransportMetadata,
    )
    from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter

    player = FakePlayer()
    adapter = VlcPlayerAdapter(FakeInstance(player), player)
    playback = ResolvedPlayback(
        URL("https://stream.example.test/live.m3u8?token=secret"),
        TransportMetadata(
            headers=(
                TransportHeader("Cookie", "session=secret; path=/"),
                TransportHeader("X-Provider-Route", "edge:a; b"),
            ),
            user_agent="SamoTech; Agent",
            referrer="https://portal.example.test/ref?token=secret",
        ),
        resource=PlaybackResource.live("provider-safe", "channel-safe"),
    )

    await adapter.play(playback)

    assert player.media is not None
    assert player.media.options == [
        ":http-header=Cookie: session=secret; path=/",
        ":http-header=X-Provider-Route: edge:a; b",
        ":http-user-agent=SamoTech; Agent",
        ":http-referrer=https://portal.example.test/ref?token=secret",
        ":network-caching=1000",
    ]
    assert "provider_id=provider-safe" in caplog.text
    assert "media_type=live" in caplog.text
    assert "content_id=channel-safe" in caplog.text
    assert "transport_type=https" in caplog.text
    assert "secret" not in caplog.text
    await adapter.close()


@pytest.mark.asyncio
async def test_resolved_playback_passes_typed_transport_metadata_to_media() -> None:
    """Transport data reaches libVLC only through the resolved playback boundary."""
    from samotech_iptv.application.dtos.playback import (
        ResolvedPlayback,
        TransportHeader,
        TransportMetadata,
    )
    from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter

    player = FakePlayer()
    adapter = VlcPlayerAdapter(FakeInstance(player), player)
    playback = ResolvedPlayback(
        URL("https://stream.example.test/live.m3u8"),
        TransportMetadata(
            headers=(TransportHeader("X-Stream-Profile", "live"),),
            user_agent="SamoTech-Test",
            referrer="https://portal.example.test/",
        ),
    )

    await adapter.play(playback)

    assert player.media is not None
    assert player.media.url == "https://stream.example.test/live.m3u8"
    assert player.media.options == [
        ":http-header=X-Stream-Profile: live",
        ":http-user-agent=SamoTech-Test",
        ":http-referrer=https://portal.example.test/",
        ":network-caching=1000",
    ]


def test_transport_metadata_rejects_duplicate_or_line_break_headers() -> None:
    from samotech_iptv.application.dtos.playback import TransportHeader, TransportMetadata
    from samotech_iptv.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        TransportHeader("X-Test\n", "value")
    with pytest.raises(ValidationError):
        TransportMetadata(
            headers=(TransportHeader("X-Test", "one"), TransportHeader("x-test", "two"))
        )


@pytest.mark.asyncio
async def test_vlc_adapter_attaches_local_subtitle_only_for_current_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    monkeypatch.setattr(
        module.vlc,
        "MediaSlaveType",
        SimpleNamespace(subtitle="subtitle"),
        raising=False,
    )
    await adapter.play(URL("https://stream.example.test/movie.m3u8"))
    subtitle = tmp_path / "arabic.srt"
    subtitle.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\nمرحبا بالعالم\n",
        encoding="utf-8",
    )

    await adapter.attach_local_subtitle(
        subtitle,
        expected_generation=adapter.media_generation,
    )

    assert player.slaves == [("subtitle", subtitle.resolve().as_uri(), True)]
    with pytest.raises(RuntimeError, match="session changed"):
        await adapter.attach_local_subtitle(
            subtitle,
            expected_generation=adapter.media_generation + 1,
        )


@pytest.mark.asyncio
async def test_vlc_adapter_supports_bounded_subtitle_delay() -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    assert await adapter.get_subtitle_delay_ms() == 0
    await adapter.set_subtitle_delay_ms(1_500)

    assert player.subtitle_delay_us == 1_500_000
    assert await adapter.get_subtitle_delay_ms() == 1_500
    with pytest.raises(ValueError, match="between -5000 and 5000"):
        await adapter.set_subtitle_delay_ms(5_001)
