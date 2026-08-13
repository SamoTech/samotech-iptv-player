"""Tests for the PySide6 desktop composition factory."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference


class FakeApplication:
    """Minimal QApplication double with process-wide instance behavior."""

    current: FakeApplication | None = None

    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
        self.styles: list[str] = []
        type(self).current = self

    @classmethod
    def instance(cls) -> FakeApplication | None:
        return cls.current

    def setStyleSheet(self, style: str) -> None:  # noqa: N802
        self.styles.append(style)


class FakeFrame:
    """Minimal QFrame double for hosted video surface construction."""

    def __init__(self) -> None:
        return None

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, _: str) -> None:  # noqa: N802
        return None

    def winId(self) -> int:  # noqa: N802
        return 1

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakeSignal:
    """Minimal Qt signal double for main-window action construction."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeAction:
    """Minimal QAction double for main-window action construction."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double for main-window action construction."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.actions: list[FakeAction] = []

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeMenuBar:
    """Minimal QMenuBar double for main-window action construction."""

    def __init__(self) -> None:
        self.menus: list[FakeMenu] = []

    def addMenu(self, title: str) -> FakeMenu:  # noqa: N802
        menu = FakeMenu(title)
        self.menus.append(menu)
        return menu


class FakeStatusBar:
    """Minimal QStatusBar double for recording status feedback."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.messages.append(message)


class FakeMainWindow:
    """Minimal QMainWindow double for bootstrap construction."""

    def __init__(self) -> None:
        self.menu_bar = FakeMenuBar()
        self.status_bar = FakeStatusBar()

    def setCentralWidget(self, _: object) -> None:  # noqa: N802
        return None

    def setWindowTitle(self, _: str) -> None:  # noqa: N802
        return None

    def menuBar(self) -> FakeMenuBar:  # noqa: N802
        return self.menu_bar

    def statusBar(self) -> FakeStatusBar:  # noqa: N802
        return self.status_bar


def _install_fake_runtime() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_NativeWindow=object()))
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QApplication = FakeApplication
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QDialog = object
    qtwidgets.QFormLayout = object
    qtwidgets.QLabel = object
    qtwidgets.QLineEdit = object
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: None))


_install_fake_runtime()

from samotech_iptv.desktop_bootstrap import build_desktop_application  # noqa: E402


class FakeRegistration:
    """Registration-use-case double used only for desktop composition."""

    async def execute(self, _: object) -> object:
        return object()


class FakePlayChannel:
    """Application playback double used only for desktop composition."""

    async def execute(self, _: str) -> None:
        return None


def test_bootstrap_composes_qt_application_vlc_player_and_main_window() -> None:
    player = object()
    with patch("samotech_iptv.desktop_bootstrap.build_player", return_value=player) as factory:
        desktop = build_desktop_application(
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakePlayChannel(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            FakeRegistration(),  # type: ignore[arg-type]
            initial_theme=ThemePreference.DARK,
            argv=["iptv-player"],
            player=player,
        )

    factory.assert_not_called()
    assert desktop.application.argv == ["iptv-player"]
    assert desktop.application.styles == ["QWidget { background-color: #202124; color: #f1f3f4; }"]
    assert desktop.main_window.video_surface._player is player
