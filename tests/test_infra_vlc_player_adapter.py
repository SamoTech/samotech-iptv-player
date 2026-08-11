"""Focused contracts for the sole libVLC player adapter."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter


class FakePlayer:
    """Deterministic libVLC player double."""

    def __init__(self) -> None:
        self.media: object | None = None
        self.playing = False
        self.calls: list[str] = []

    def is_playing(self) -> int:
        return int(self.playing)

    def set_media(self, media: object) -> None:
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


class FakeInstance:
    """Deterministic libVLC instance double."""

    def __init__(self, player: FakePlayer) -> None:
        self.player = player

    def media_player_new(self) -> FakePlayer:
        return self.player

    def media_new(self, url: str) -> object:
        return {"url": url}


def _adapter(player: FakePlayer) -> VlcPlayerAdapter:
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: FakeInstance(player)))
    module = importlib.import_module("samotech_iptv.infrastructure.player.vlc_player_adapter")
    return module.VlcPlayerAdapter(FakeInstance(player), player)


@pytest.mark.asyncio
async def test_vlc_adapter_controls_libvlc_playback() -> None:
    player = FakePlayer()
    adapter = _adapter(player)

    await adapter.play(URL("https://example.test/live.m3u8"))
    assert adapter.is_playing is True
    assert player.media == {"url": "https://example.test/live.m3u8"}

    await adapter.pause()
    assert adapter.is_playing is False
    await adapter.resume()
    await adapter.stop()

    assert player.calls == ["play", "pause", "play", "stop"]
