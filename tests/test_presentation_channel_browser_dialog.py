from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos import ChannelDTO, LoadChannelsResponse


class FakeSignal:
    """Minimal Qt signal double retaining connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeAction:
    """Minimal QAction double for other presentation modules imported during collection."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double recording menu actions."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.actions: list[FakeAction] = []

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeMenuBar:
    """Minimal QMenuBar double recording application menus."""

    def __init__(self) -> None:
        self.menus: list[FakeMenu] = []

    def addMenu(self, title: str) -> FakeMenu:  # noqa: N802
        menu = FakeMenu(title)
        self.menus.append(menu)
        return menu


class FakeFrame:
    """Minimal QFrame double for the native video surface imported by the main window."""

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, _: str) -> None:  # noqa: N802
        return None

    def winId(self) -> int:  # noqa: N802
        return 1


class FakeMainWindow:
    """Minimal QMainWindow double for cross-module import compatibility."""

    def __init__(self) -> None:
        self.central_widget: object | None = None
        self.menu_bar = FakeMenuBar()
        self.title: str | None = None

    def setCentralWidget(self, widget: object) -> None:  # noqa: N802
        self.central_widget = widget

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def menuBar(self) -> FakeMenuBar:  # noqa: N802
        return self.menu_bar


class FakeApplication:
    """Minimal QApplication double for desktop-bootstrap import compatibility."""

    @classmethod
    def instance(cls) -> None:
        return None

    def __init__(self, argv: list[str]) -> None:
        self.argv = argv


class FakeDialog:
    """Minimal QDialog double retaining the configured window title."""

    def __init__(self) -> None:
        self.title: str | None = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title


class FakeFormLayout:
    """Minimal QFormLayout double recording dialog rows."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double retaining safe status feedback."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double compatible with all provider-entry dialogs."""

    class EchoMode:
        """Minimal echo-mode namespace for password fields."""

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


class FakeListWidget:
    """Minimal QListWidget double recording selectable channel summary rows."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def addItem(self, item: str) -> None:  # noqa: N802
        self.items.append(item)

    def clear(self) -> None:
        self.items.clear()


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = type(
        "Qt", (), {"WidgetAttribute": type("WidgetAttribute", (), {"WA_NativeWindow": object()})}
    )
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QApplication = FakeApplication
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QListWidget = FakeListWidget
    qtwidgets.QMainWindow = FakeMainWindow
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.channel_browser_dialog import (  # noqa: E402
    ChannelBrowserDialog,
)


class FakeBrowseChannels:
    """Use-case double returning a configured safe browser response."""

    def __init__(self, response: LoadChannelsResponse) -> None:
        self.response = response
        self.provider_ids: list[str] = []

    async def execute(self, request: object) -> LoadChannelsResponse:
        self.provider_ids.append(request.provider_id)  # type: ignore[union-attr]
        return self.response


@pytest.mark.asyncio
async def test_channel_browser_renders_only_channel_name_and_stream_id() -> None:
    browser = FakeBrowseChannels(
        LoadChannelsResponse(
            channels=[
                ChannelDTO(
                    id="internal-channel-id",
                    name="News HD",
                    provider_id="provider-one",
                    stream_id="1234",
                    logo_url="https://example.invalid/logo.png",
                )
            ],
            total=1,
        )
    )
    dialog = ChannelBrowserDialog(browser)  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"

    response = await dialog.load_channels()

    assert response.total == 1
    assert browser.provider_ids == ["provider-one"]
    assert dialog.channel_list.items == ["News HD · 1234"]
    assert dialog.status_label.value == "1 channels loaded"
    assert "internal-channel-id" not in dialog.channel_list.items[0]
    assert "https://" not in dialog.channel_list.items[0]


@pytest.mark.asyncio
async def test_channel_browser_hides_provider_error_details() -> None:
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(LoadChannelsResponse(error="https://token.example/?secret=value"))
    )  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"

    await dialog.load_channels()

    assert dialog.channel_list.items == []
    assert dialog.status_label.value == "Unable to load channels"
    assert "secret" not in dialog.status_label.value
