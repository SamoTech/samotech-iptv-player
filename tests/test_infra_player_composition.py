"""Tests for VLC-only player composition."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: None))

from samotech_iptv.infrastructure.player.composition import build_player  # noqa: E402


def test_build_player_constructs_the_vlc_adapter() -> None:
    with patch(
        "samotech_iptv.infrastructure.player.composition.VlcPlayerAdapter",
        autospec=True,
    ) as adapter_type:
        player = build_player()

    adapter_type.assert_called_once_with()
    assert player is adapter_type.return_value
