"""VLC-only player composition helpers."""

from __future__ import annotations

from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter

__all__ = ["build_player"]


def build_player() -> VlcPlayerAdapter:
    """Construct the application's sole supported libVLC player backend."""
    return VlcPlayerAdapter()
