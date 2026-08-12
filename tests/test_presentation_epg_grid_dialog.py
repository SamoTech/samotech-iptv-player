from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos import EPGEntryDTO, LoadEPGResponse


class FakeAction:
    """Minimal QAction double compatible with later main-window collection."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double recording composed actions."""

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


class FakeApplication:
    """Minimal QApplication double compatible with bootstrap collection."""

    current: FakeApplication | None = None

    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
        type(self).current = self

    @classmethod
    def instance(cls) -> FakeApplication | None:
        return cls.current


class FakeFrame:
    """Minimal QFrame double compatible with native video-surface construction."""

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, _: str) -> None:  # noqa: N802
        return None

    def winId(self) -> int:  # noqa: N802
        return 1

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakeMainWindow:
    """Minimal QMainWindow double compatible with later composition collection."""

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


class FakeSignal:
    """Minimal Qt signal double retaining connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


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
    """Minimal QLabel double retaining status feedback."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double retaining entered safe identifiers."""

    def __init__(self) -> None:
        self.value = ""

    def text(self) -> str:
        return self.value


class FakeListWidget:
    """Minimal QListWidget double recording rendered programme rows."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def addItem(self, item: str) -> None:  # noqa: N802
        self.items.append(item)

    def clear(self) -> None:
        self.items.clear()


class FakePushButton:
    """Minimal QPushButton double exposing its clicked signal."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()


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
    qtwidgets.QPushButton = FakePushButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.epg_grid_dialog import EPGGridDialog  # noqa: E402


class FakeLoadRegisteredEPG:
    """Use-case double retaining the provider and channel selection request."""

    def __init__(self, response: LoadEPGResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    async def execute(self, request: object) -> LoadEPGResponse:
        self.requests.append(request)
        return self.response


@pytest.mark.asyncio
async def test_epg_grid_renders_only_title_and_schedule_data() -> None:
    loader = FakeLoadRegisteredEPG(
        LoadEPGResponse(
            entries=[
                EPGEntryDTO(
                    id="internal-programme-id",
                    channel_id="internal-channel-id",
                    title="Morning News",
                    start="2026-08-12T10:00:00+00:00",
                    end="2026-08-12T10:30:00+00:00",
                    description="https://example.invalid/private-guide",
                )
            ]
        )
    )
    dialog = EPGGridDialog(loader)  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"
    dialog.channel_id_input.value = "channel-one"

    response = await dialog.load_epg()

    assert response.error is None
    assert loader.requests[0].provider_id == "provider-one"  # type: ignore[union-attr]
    assert loader.requests[0].channel_id == "channel-one"  # type: ignore[union-attr]
    assert dialog.epg_list.items == [
        "2026-08-12T10:00:00+00:00 – 2026-08-12T10:30:00+00:00 · Morning News"
    ]
    assert dialog.status_label.value == "1 programmes loaded"
    assert "internal-programme-id" not in dialog.epg_list.items[0]
    assert "internal-channel-id" not in dialog.epg_list.items[0]
    assert "example.invalid" not in dialog.epg_list.items[0]


@pytest.mark.asyncio
async def test_epg_grid_replaces_error_details_with_safe_status() -> None:
    dialog = EPGGridDialog(FakeLoadRegisteredEPG(LoadEPGResponse(error="request failed")))  # type: ignore[arg-type]

    response = await dialog.load_epg()

    assert response.error == "request failed"
    assert dialog.epg_list.items == []
    assert dialog.status_label.value == "Unable to load EPG"
