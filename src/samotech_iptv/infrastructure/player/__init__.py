"""Infrastructure player adapters.

The application supports libVLC through ``VlcPlayerAdapter`` as its sole
playback backend.
"""

from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter

__all__ = ["VlcPlayerAdapter"]
