"""Tests for the PySide6 native libVLC video surface."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace


class FakeFrame:
    """Minimal QFrame double with a stable native window identifier."""

    def __init__(self) -> None:
        self.attributes: list[object] = []
        self.styles: list[str] = []

    def setAttribute(self, attribute: object) -> None:  # noqa: N802
        self.attributes.append(attribute)

    def setStyleSheet(self, style: str) -> None:  # noqa: N802
        self.styles.append(style)

    def winId(self) -> int:  # noqa: N802
        return 456

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakePlayer:
    """Player-port double that records native-output attachment calls."""

    def __init__(self) -> None:
        self.native_window_ids: list[int] = []

    def attach_video_output(self, native_window_id: int) -> None:
        self.native_window_ids.append(native_window_id)


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_NativeWindow=object()))
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QFrame = FakeFrame
    sys.modules.setdefault("PySide6", ModuleType("PySide6"))
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtGui", qtgui)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)


_install_fake_pyside6()

from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface  # noqa: E402


def test_video_surface_attaches_native_handle_once() -> None:
    player = FakePlayer()
    surface = VlcVideoSurface(player)  # type: ignore[arg-type]

    surface.attach_player_output()
    surface.attach_player_output()

    assert player.native_window_ids == [int(surface.winId())]
