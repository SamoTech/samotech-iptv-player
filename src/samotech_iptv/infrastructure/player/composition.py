"""VLC-only player composition helpers."""

from __future__ import annotations

from samotech_iptv.infrastructure.player.vlc_player_adapter import (
    PlaybackMode,
    VlcPlayerAdapter,
)

__all__ = ["build_player"]


def build_player(*, buffer_size_mb: int = 16, hardware_decode: bool = True) -> VlcPlayerAdapter:
    """Construct the libVLC backend from the application player settings.

    VLC exposes live-stream buffering in milliseconds while the application
    configuration expresses the setting as a coarse buffer size in megabytes.
    A one-second-per-megabyte mapping keeps the existing setting meaningful and
    clamps the result to a conservative one-second minimum.
    """
    playback_mode: PlaybackMode = "auto" if hardware_decode else "software"
    network_caching_ms = max(1_000, buffer_size_mb * 1_000)
    return VlcPlayerAdapter(
        playback_mode=playback_mode,
        network_caching_ms=network_caching_ms,
    )
