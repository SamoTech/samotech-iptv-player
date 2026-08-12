"""Tests for the initial PySide6 VLC playback main window."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest


class FakeFrame:
    """Minimal QFrame double for the hosted native video surface."""

    def __init__(self) -> None:
        self.styles: list[str] = []

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, style: str) -> None:  # noqa: N802
        self.styles.append(style)

    def winId(self) -> int:  # noqa: N802
        return 789

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakeMainWindow:
    """Minimal QMainWindow double for composition verification."""

    def __init__(self) -> None:
        self.central_widget: object | None = None
        self.title: str | None = None

    def setCentralWidget(self, widget: object) -> None:  # noqa: N802
        self.central_widget = widget

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title


class FakePlayer:
    """Player-port double that records native output attachment."""

    def __init__(self) -> None:
        self.native_window_ids: list[int] = []

    def attach_video_output(self, native_window_id: int) -> None:
        self.native_window_ids.append(native_window_id)


class FakeRegistration:
    """Registration-use-case double required by main-window composition."""

    async def execute(self, _: object) -> object:
        return object()


class FakePlayChannel:
    """Application-use-case double that records presentation requests."""

    def __init__(self) -> None:
        self.channel_ids: list[str] = []

    async def execute(self, channel_id: str) -> None:
        self.channel_ids.append(channel_id)


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_NativeWindow=object()))
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QDialog = object
    qtwidgets.QFormLayout = object
    qtwidgets.QLineEdit = object
    sys.modules.setdefault("PySide6", ModuleType("PySide6"))
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtGui", qtgui)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)


_install_fake_pyside6()

from samotech_iptv.presentation.views.main_window import MainWindow  # noqa: E402


@pytest.mark.asyncio
async def test_main_window_attaches_surface_then_delegates_playback() -> None:
    player = FakePlayer()
    play_channel = FakePlayChannel()
    window = MainWindow(player, play_channel, FakeRegistration())  # type: ignore[arg-type]

    await window.play_channel("xtream-demo:1")

    assert player.native_window_ids == [int(window.video_surface.winId())]
    assert play_channel.channel_ids == ["xtream-demo:1"]
