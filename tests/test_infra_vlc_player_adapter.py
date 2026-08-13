from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

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


class FakeInstance:
    """Deterministic libVLC instance double."""

    def __init__(self, player: FakePlayer) -> None:
        self.player = player

    def media_player_new(self) -> FakePlayer:
        return self.player

    def media_new(self, url: str) -> FakeMedia:
        return FakeMedia(url)


def _adapter(player: FakePlayer, **kwargs: object) -> VlcPlayerAdapter:
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: FakeInstance(player)))
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    return module.VlcPlayerAdapter(FakeInstance(player), player, **kwargs)


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


def test_vlc_adapter_attaches_linux_video_output(monkeypatch: pytest.MonkeyPatch) -> None:
    player = FakePlayer()
    adapter = _adapter(player)
    monkeypatch.setattr(
        "samotech_iptv.infrastructure.player.vlc_player_adapter.sys.platform", "linux"
    )

    adapter.attach_video_output(1234)

    assert player.calls == ["xwindow:1234"]
