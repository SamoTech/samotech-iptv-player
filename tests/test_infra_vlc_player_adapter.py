from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos.playback import PlaybackOutcome, PlaybackTarget
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


class FakePlayer:
    """Deterministic libVLC player double."""

    def __init__(self) -> None:
        self.media: FakeMedia | None = None
        self.playing = False
        self.calls: list[str] = []

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

    await adapter.play(URL("https://example.test/live.m3u8"))
    assert adapter.is_playing is True
    assert player.media is not None
    assert player.media.url == "https://example.test/live.m3u8"
    assert player.media.options == [":network-caching=1000"]

    await adapter.pause()
    assert adapter.is_playing is False
    await adapter.resume()
    await adapter.stop()

    assert player.calls == ["play", "pause", "play", "stop"]


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
    assert player.media.options == [
        f":sout=#duplicate{{dst=display,dst=std{{access=file,mux=ts,dst='{destination}'}}}}"
    ]
    assert player.calls == ["play", "play"]

    await adapter.stop_recording()

    assert adapter.is_recording is False
    assert player.media is not None
    assert player.media.url == "https://example.test/live.m3u8"
    assert player.media.options == [":network-caching=1000"]
    assert player.calls == ["play", "play", "play"]


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

    assert player.calls == ["play", "play"]
    assert adapter._media_generation == 2
    await adapter.close()


@pytest.mark.asyncio
async def test_unexpected_stopped_rebuilds_live_media_once(monkeypatch: pytest.MonkeyPatch) -> None:
    player = EventPlayer()
    adapter, event_types = _event_adapter(monkeypatch, player, live_recovery_initial_delay_s=0)

    await adapter.play(URL("https://example.test/live.m3u8"))
    player.events.emit(event_types.MediaPlayerStopped)
    await _flush_asyncio()

    assert player.calls == ["play", "play"]
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

    assert player.calls == ["play", "play"]
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

    assert player.calls == ["play", "play"]
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

    assert player.calls == ["play", "play"]
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

    assert player.calls == ["play", "play"]
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
