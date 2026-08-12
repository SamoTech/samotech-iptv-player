"""Tests for the production desktop composition root."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.database.sqlite_theme_preference_repository import (
    SQLiteThemePreferenceRepository,
)
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


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


class FakeDialog:
    """Minimal QDialog double for lazy dialog imports."""

    def setWindowTitle(self, _: str) -> None:  # noqa: N802
        return None

    def show(self) -> None:
        return None


class FakeFormLayout:
    """Minimal QFormLayout double for lazy dialog imports."""

    def __init__(self, _: object) -> None:
        return None

    def addRow(self, *_: object) -> None:  # noqa: N802
        return None


class FakeLabel:
    """Minimal QLabel double for lazy dialog imports."""

    def setText(self, _: str) -> None:  # noqa: N802
        return None


class FakeLineEdit:
    """Minimal QLineEdit double for lazy dialog imports."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def text(self) -> str:
        return self.value


class FakeButton:
    """Minimal QPushButton double for lazy dialog imports."""

    def __init__(self, _: str) -> None:
        self.clicked = FakeSignal()


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

    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.messages.append(message)


class FakeMainWindow:
    """Minimal QMainWindow double for desktop construction."""

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


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_NativeWindow=object()))
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QApplication = FakeApplication
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    sys.modules.setdefault("vlc", SimpleNamespace(Instance=lambda: None))


_install_fake_pyside6()

from samotech_iptv.desktop_bootstrap import DesktopApplication  # noqa: E402
from samotech_iptv.desktop_composition import (  # noqa: E402
    build_production_desktop_application,
)


@pytest.mark.asyncio
async def test_production_composition_initialises_state_restores_metadata_and_wires_desktop(
    tmp_path: Path,
) -> None:
    """Composition restores safe state and gives every playback use case one player."""
    data_directory = tmp_path / "application-data"
    database_path = data_directory / "samotech_iptv.sqlite3"
    metadata_repository = SQLiteProviderMetadataRepository(database_path)
    theme_repository = SQLiteThemePreferenceRepository(database_path)
    await metadata_repository.initialise()
    await theme_repository.initialise()
    await metadata_repository.save(
        InfraProviderMetadata(
            provider_id="saved-playlist",
            provider_type="m3u",
            base_url="https://example.test/playlist.m3u",
        )
    )
    await theme_repository.save(ThemePreference.DARK)

    player = object()
    desktop = DesktopApplication(application=object(), main_window=object())
    with (
        patch(
            "samotech_iptv.desktop_composition.build_player", return_value=player
        ) as player_factory,
        patch(
            "samotech_iptv.desktop_composition.build_desktop_application",
            return_value=desktop,
        ) as desktop_factory,
    ):
        result = await build_production_desktop_application(
            argv=["samotech-iptv"],
            config_overrides={"data_dir": str(data_directory)},
        )

    assert result.application is desktop.application
    assert result.main_window is desktop.main_window
    assert result.close is not None
    player_factory.assert_called_once_with()
    arguments = desktop_factory.call_args.args
    keywords = desktop_factory.call_args.kwargs
    assert keywords["argv"] == ["samotech-iptv"]
    assert keywords["initial_theme"] is ThemePreference.DARK
    assert keywords["player"] is player
    assert arguments[3]._provider_catalog._registry.list_all() == [  # noqa: SLF001
        InfraProviderMetadata(
            provider_id="saved-playlist",
            provider_type="m3u",
            base_url="https://example.test/playlist.m3u",
        )
    ]
    assert arguments[4]._provider_resolver is arguments[7]._provider_resolver  # noqa: SLF001
    assert arguments[5]._registration is arguments[6]._registration  # noqa: SLF001
    assert arguments[7]._provider_resolver._factory.supported_types() == {  # noqa: SLF001
        "m3u",
        "mag",
        "xtream",
    }
    assert arguments[8]._player is player  # noqa: SLF001
    assert arguments[14]._player is player  # noqa: SLF001
    assert arguments[15]._player is player  # noqa: SLF001
    assert arguments[16]._player is player  # noqa: SLF001
    assert arguments[17]._player is player  # noqa: SLF001
    assert arguments[18]._player is player  # noqa: SLF001
