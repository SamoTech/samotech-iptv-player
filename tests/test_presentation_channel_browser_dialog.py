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


class FakeModelIndex:
    """Minimal QModelIndex double for model and selection tests."""

    def __init__(self, row: int = -1, valid: bool | None = None) -> None:
        self._row = row
        self._valid = row >= 0 if valid is None else valid

    def isValid(self) -> bool:  # noqa: N802
        return self._valid

    def row(self) -> int:
        return self._row


class FakeAbstractListModel:
    """Minimal QAbstractListModel double recording reset batches."""

    def __init__(self) -> None:
        self.reset_count = 0

    def beginResetModel(self) -> None:  # noqa: N802
        self.reset_count += 1

    def endResetModel(self) -> None:  # noqa: N802
        return None


class FakeListView:
    """Minimal QListView double exposing model-backed selection."""

    def __init__(self) -> None:
        self.model: object | None = None
        self.current_row = -1
        self.doubleClicked = FakeSignal()  # noqa: N815

    def setModel(self, model: object) -> None:  # noqa: N802
        self.model = model

    def currentIndex(self) -> FakeModelIndex:  # noqa: N802
        return FakeModelIndex(self.current_row)


class FakePushButton:
    """Minimal QPushButton double exposing its clicked signal."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.QAbstractListModel = FakeAbstractListModel
    qtcore.QModelIndex = FakeModelIndex
    qtcore.Qt = type(
        "Qt",
        (),
        {
            "ItemDataRole": type("ItemDataRole", (), {"DisplayRole": 0}),
            "WidgetAttribute": type("WidgetAttribute", (), {"WA_NativeWindow": object()}),
        },
    )
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QApplication = FakeApplication
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QListView = FakeListView
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QPushButton = FakePushButton
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
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 1
    assert dialog.channel_model.data(FakeModelIndex(0), 0) == "News HD · 1234"
    assert dialog.status_label.value == "1 channels loaded"
    assert "internal-channel-id" not in dialog.channel_model.data(FakeModelIndex(0), 0)
    assert "https://" not in dialog.channel_model.data(FakeModelIndex(0), 0)
    assert dialog.channel_model.reset_count == 1


@pytest.mark.asyncio
async def test_channel_browser_model_handles_39753_rows_in_one_reset() -> None:
    channel = ChannelDTO(
        id="channel-1",
        name="Large Catalogue Channel",
        provider_id="provider-one",
        stream_id="stream-1",
    )
    channels = [channel] * 39_753
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(LoadChannelsResponse(channels=channels, total=len(channels)))
    )  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"

    response = await dialog.load_channels()

    assert response.total == 39_753
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 39_753
    assert dialog.channel_model.reset_count == 1
    assert dialog.channel_model.data(FakeModelIndex(0), 0) == ("Large Catalogue Channel · stream-1")
    assert dialog.channel_model.data(FakeModelIndex(19_876), 0) == (
        "Large Catalogue Channel · stream-1"
    )
    assert dialog.channel_model.data(FakeModelIndex(39_752), 0) == (
        "Large Catalogue Channel · stream-1"
    )
    for row in (0, 19_876, 39_752):
        selected = dialog.channel_model.channel_at(row)
        assert selected.provider_id == "provider-one"
        assert selected.id == "channel-1"
    dialog.channel_model.replace_channels([channel])
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 1
    assert dialog.channel_model.reset_count == 2
    assert not hasattr(dialog.channel_list, "addItem")


@pytest.mark.asyncio
async def test_channel_browser_model_handles_empty_and_blank_display_values() -> None:
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(
            LoadChannelsResponse(
                channels=[
                    ChannelDTO(
                        id="blank-channel",
                        name="",
                        provider_id="provider-one",
                        stream_id="",
                    )
                ],
                total=1,
            )
        )
    )  # type: ignore[arg-type]

    await dialog.load_channels()
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 1
    assert dialog.channel_model.data(FakeModelIndex(0), 0) == " · "

    dialog.channel_model.replace_channels([])
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 0
    assert dialog.channel_model.reset_count == 2


@pytest.mark.asyncio
async def test_channel_browser_hides_provider_error_details() -> None:
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(LoadChannelsResponse(error="https://token.example/?secret=value"))
    )  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"

    await dialog.load_channels()

    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 0
    assert dialog.status_label.value == "Unable to load channels"
    assert "secret" not in dialog.status_label.value


class FakePlaySelectedChannel:
    """Playback callback double recording safe selected-provider channel identifiers."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    async def __call__(self, provider_id: str, channel_id: str) -> None:
        self.requests.append((provider_id, channel_id))


@pytest.mark.asyncio
async def test_channel_browser_delegates_selected_channel_to_playback_callback() -> None:
    playback = FakePlaySelectedChannel()
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(
            LoadChannelsResponse(
                channels=[
                    ChannelDTO(
                        id="channel-7",
                        name="Sports HD",
                        provider_id="provider-one",
                        stream_id="stream-7",
                    )
                ],
                total=1,
            )
        ),
        playback,
    )  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"

    await dialog.load_channels()
    await dialog._play_channel(0)

    assert playback.requests == [("provider-one", "channel-7")]
    assert dialog.status_label.value == "Playing Sports HD"
    assert "stream-7" not in dialog.status_label.value


class FakeSearchRegisteredChannels:
    """Search use-case double retaining only the provider ID and query passed by the UI."""

    def __init__(self, response: LoadChannelsResponse) -> None:
        self.response = response
        self.requests: list[tuple[str, str]] = []

    async def execute(self, request: object) -> LoadChannelsResponse:
        self.requests.append((request.provider_id, request.query))  # type: ignore[union-attr]
        return self.response


@pytest.mark.asyncio
async def test_channel_browser_search_renders_safe_matching_rows() -> None:
    search = FakeSearchRegisteredChannels(
        LoadChannelsResponse(
            channels=[
                ChannelDTO(
                    id="internal-channel-id",
                    name="Sports News",
                    provider_id="provider-one",
                    stream_id="900",
                )
            ],
            total=1,
        )
    )
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(LoadChannelsResponse()),
        search_channels=search,  # type: ignore[arg-type]
    )  # type: ignore[arg-type]
    dialog.provider_id_input.value = "provider-one"
    dialog.search_query_input.value = "sports"

    await dialog.search_channels()

    assert search.requests == [("provider-one", "sports")]
    assert dialog.channel_model.rowCount(FakeModelIndex(valid=False)) == 1
    assert dialog.channel_model.data(FakeModelIndex(0), 0) == "Sports News · 900"
    assert dialog.status_label.value == "1 channels found"
    assert "internal-channel-id" not in dialog.channel_model.data(FakeModelIndex(0), 0)


class FakeSaveFavorite:
    """Favorite use-case double recording the safe selected item identifier."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    async def execute(self, request: object) -> object:
        self.requests.append((request.item_id, request.item_type))  # type: ignore[union-attr]
        return type("Response", (), {"success": True})()


@pytest.mark.asyncio
async def test_channel_browser_saves_selected_channel_as_favorite() -> None:
    save_favorite = FakeSaveFavorite()
    dialog = ChannelBrowserDialog(
        FakeBrowseChannels(
            LoadChannelsResponse(
                channels=[
                    ChannelDTO(
                        id="channel-9",
                        name="Documentary HD",
                        provider_id="provider-one",
                        stream_id="stream-9",
                    )
                ],
                total=1,
            )
        ),
        save_favorite=save_favorite,  # type: ignore[arg-type]
    )  # type: ignore[arg-type]

    await dialog.load_channels()
    await dialog.add_favorite(0)

    assert save_favorite.requests == [("channel-9", "channel")]
    assert dialog.status_label.value == "Channel added to favorites"
    assert "stream-9" not in dialog.status_label.value
