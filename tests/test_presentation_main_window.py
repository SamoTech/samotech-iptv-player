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


class FakeDialog:
    """Minimal QDialog double for imported provider-entry dialog construction."""

    def __init__(self) -> None:
        self.title: str | None = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title


class FakeFormLayout:
    """Minimal QFormLayout double for imported provider-entry dialog construction."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double retaining dialog feedback copy."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double for imported provider-entry dialog construction."""

    class EchoMode:
        """Minimal echo-mode namespace."""

        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.echo_mode: object | None = None

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, echo_mode: object) -> None:  # noqa: N802
        self.echo_mode = echo_mode

    def text(self) -> str:
        return self.value


class FakeSignal:
    """Minimal Qt signal double that records connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeAction:
    """Minimal QAction double for menu-action composition verification."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double that records its actions."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.actions: list[FakeAction] = []

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeMenuBar:
    """Minimal QMenuBar double that records its menus."""

    def __init__(self) -> None:
        self.menus: list[FakeMenu] = []

    def addMenu(self, title: str) -> FakeMenu:  # noqa: N802
        menu = FakeMenu(title)
        self.menus.append(menu)
        return menu


class FakeMainWindow:
    """Minimal QMainWindow double for composition verification."""

    def __init__(self) -> None:
        self.central_widget: object | None = None
        self.title: str | None = None
        self.menu_bar = FakeMenuBar()

    def setCentralWidget(self, widget: object) -> None:  # noqa: N802
        self.central_widget = widget

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def menuBar(self) -> FakeMenuBar:  # noqa: N802
        return self.menu_bar


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
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
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
    window = MainWindow(
        player,
        play_channel,
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
    )  # type: ignore[arg-type]

    await window.play_channel("xtream-demo:1")

    assert player.native_window_ids == [int(window.video_surface.winId())]
    assert play_channel.channel_ids == ["xtream-demo:1"]


def test_main_window_exposes_xtream_provider_menu_action() -> None:
    window = MainWindow(
        FakePlayer(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
    )  # type: ignore[arg-type]

    assert window.menu_bar.menus[0].title == "Providers"
    assert window.menu_bar.menus[0].actions == [
        window.add_xtream_provider_action,
        window.add_m3u_provider_action,
        window.add_mag_provider_action,
        window.browse_channels_action,
        window.show_provider_list_action,
    ]
    assert window.add_xtream_provider_action.text == "Add Xtream Provider…"
    assert window.add_xtream_provider_action.triggered.callbacks == [
        window.open_xtream_provider_dialog
    ]
    assert window.add_m3u_provider_action.text == "Add M3U Provider…"
    assert window.add_m3u_provider_action.triggered.callbacks == [window.open_m3u_provider_dialog]
    assert window.add_mag_provider_action.text == "Add MAG/Stalker Provider…"
    assert window.add_mag_provider_action.triggered.callbacks == [window.open_mag_provider_dialog]
    assert window.browse_channels_action.text == "Browse Channels"
    assert window.browse_channels_action.triggered.callbacks == [window.open_channel_browser_dialog]
    assert window.show_provider_list_action.text == "Show Registered Providers"
    assert window.show_provider_list_action.triggered.callbacks == [
        window.open_provider_list_dialog
    ]
