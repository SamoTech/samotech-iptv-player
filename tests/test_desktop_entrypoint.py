"""Tests for the supported desktop lifecycle entry point."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


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
    """Minimal QFrame double for video-surface construction."""

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, _: str) -> None:  # noqa: N802
        return None

    def winId(self) -> int:  # noqa: N802
        return 1

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakeSignal:
    """Minimal Qt signal double for action construction."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeAction:
    """Minimal QAction double for main-window construction."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double for main-window construction."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.actions: list[FakeAction] = []

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeMenuBar:
    """Minimal QMenuBar double for main-window construction."""

    def __init__(self) -> None:
        self.menus: list[FakeMenu] = []

    def addMenu(self, title: str) -> FakeMenu:  # noqa: N802
        menu = FakeMenu(title)
        self.menus.append(menu)
        return menu


class FakeStatusBar:
    """Minimal QStatusBar double for main-window construction."""

    def showMessage(self, _: str) -> None:  # noqa: N802
        return None


class FakeMainWindow:
    """Minimal QMainWindow double for main-window construction."""

    def __init__(self) -> None:
        self._menu_bar = FakeMenuBar()
        self._status_bar = FakeStatusBar()

    def setCentralWidget(self, _: object) -> None:  # noqa: N802
        return None

    def setWindowTitle(self, _: str) -> None:  # noqa: N802
        return None

    def menuBar(self) -> FakeMenuBar:  # noqa: N802
        return self._menu_bar

    def statusBar(self) -> FakeStatusBar:  # noqa: N802
        return self._status_bar


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
    qtwidgets.QPushButton = object
    sys.modules.setdefault("PySide6", ModuleType("PySide6"))
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtGui", qtgui)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: None))


_install_fake_runtime()

from samotech_iptv import desktop_entrypoint  # noqa: E402


def test_entrypoint_composes_then_runs_desktop(monkeypatch: MonkeyPatch) -> None:
    """The supported entry point delegates argv through production composition."""
    desktop = object()
    received_arguments: list[list[str]] = []

    async def build(arguments: list[str]) -> object:
        received_arguments.append(arguments)
        return desktop

    monkeypatch.setattr(desktop_entrypoint, "build_production_desktop_application", build)
    monkeypatch.setattr(
        desktop_entrypoint, "run_desktop_application", lambda value: value is desktop
    )

    assert desktop_entrypoint.run(["samotech-iptv", "--example"]) is True
    assert received_arguments == [["samotech-iptv", "--example"]]


def test_entrypoint_hides_startup_exception_details(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    """A startup error is generic and never echoes the underlying detail."""

    async def fail(_: list[str]) -> object:
        raise RuntimeError("secret tokenized provider URL")

    monkeypatch.setattr(desktop_entrypoint, "build_production_desktop_application", fail)

    assert desktop_entrypoint.run(["samotech-iptv"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Unable to start SamoTech IPTV Player\n"
    assert "secret" not in captured.err
