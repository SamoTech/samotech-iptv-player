"""Regression coverage for provider-add Save/Cancel actions and safe submission."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos.provider_registration import (
    RegisterXtreamProviderResponse,
)


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeDialog:
    def __init__(self) -> None:
        self.accepted = False
        self.rejected = False

    def setWindowTitle(self, _: str) -> None:  # noqa: N802
        pass

    def accept(self) -> None:
        self.accepted = True

    def reject(self) -> None:
        self.rejected = True


class FakeFormLayout:
    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    class EchoMode:
        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.echo_mode: object | None = None

    def setEchoMode(self, mode: object) -> None:  # noqa: N802
        self.echo_mode = mode

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def text(self) -> str:
        return self.value

    def clear(self) -> None:
        self.value = ""

    def setPlaceholderText(self, _: str) -> None:  # noqa: N802
        return None

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None

    def setToolTip(self, _: str) -> None:  # noqa: N802
        return None


class FakeButton:
    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        self.enabled = enabled

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None


class FakeFileDialog:
    selected_path = ""

    @classmethod
    def getOpenFileName(cls, *_: object) -> tuple[str, str]:  # noqa: N802
        return cls.selected_path, ""


original_pyside = sys.modules.get("PySide6")
original_widgets = sys.modules.get("PySide6.QtWidgets")
widgets = ModuleType("PySide6.QtWidgets")
widgets.QDialog = FakeDialog
widgets.QFormLayout = FakeFormLayout
widgets.QLabel = FakeLabel
widgets.QLineEdit = FakeLineEdit
widgets.QPushButton = FakeButton
widgets.QFileDialog = FakeFileDialog
sys.modules["PySide6"] = ModuleType("PySide6")
sys.modules["PySide6.QtWidgets"] = widgets

from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog  # noqa: E402
from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog  # noqa: E402
from samotech_iptv.presentation.dialogs.xtream_provider_dialog import (  # noqa: E402
    XtreamProviderDialog,
)

if original_pyside is None:
    sys.modules.pop("PySide6", None)
else:
    sys.modules["PySide6"] = original_pyside
if original_widgets is None:
    sys.modules.pop("PySide6.QtWidgets", None)
else:
    sys.modules["PySide6.QtWidgets"] = original_widgets


class FakeRegistration:
    def __init__(self, response: RegisterXtreamProviderResponse | None = None) -> None:
        self.requests: list[object] = []
        self.response = response or RegisterXtreamProviderResponse(provider_id="saved")

    async def execute(self, request: object) -> RegisterXtreamProviderResponse:
        self.requests.append(request)
        return self.response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("dialog_type", "values"),
    [
        (M3UProviderDialog, {"source_input": "file:///playlist.m3u"}),
        (
            XtreamProviderDialog,
            {
                "base_url_input": "https://server.example",
                "username_input": "user",
                "password_input": "secret",
            },
        ),
        (
            MAGProviderDialog,
            {
                "portal_url_input": "https://portal.example",
                "mac_address_input": "00:11:22:33:44:55",
            },
        ),
    ],
)
async def test_provider_add_dialogs_have_save_cancel_and_successful_save_closes(
    dialog_type: type[object], values: dict[str, str]
) -> None:
    registration = FakeRegistration()
    dialog = dialog_type(registration)  # type: ignore[call-arg]

    if dialog_type is M3UProviderDialog:
        assert dialog.load_button.text == "Load Playlist"
        assert dialog.browse_button.text == "Browse Local File…"
    else:
        assert dialog.save_button.text == "Save"
    assert dialog.cancel_button.text == "Cancel"
    assert dialog.cancel_button.clicked.callbacks == [dialog._cancel]
    for field_name, value in values.items():
        getattr(dialog, field_name).setText(value)

    await dialog.submit()

    assert len(registration.requests) == 1
    if dialog_type is M3UProviderDialog:
        assert registration.requests[0].provider_id == "m3u-playlist"
    elif dialog_type is XtreamProviderDialog:
        assert registration.requests[0].provider_id == "xtream-server-example"
    else:
        assert registration.requests[0].provider_id == "mag-portal-example"
    assert dialog.closed_successfully is True
    assert "secret" not in dialog.status_label.value.casefold()
    assert "00:11:22:33:44:55" not in dialog.status_label.value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dialog_type", [M3UProviderDialog, XtreamProviderDialog, MAGProviderDialog]
)
async def test_provider_add_dialog_validation_does_not_persist_or_close(
    dialog_type: type[object],
) -> None:
    registration = FakeRegistration()
    dialog = dialog_type(registration)  # type: ignore[call-arg]

    await dialog.submit()

    assert registration.requests == []
    assert dialog.closed_successfully is False
    expected = "playlist" if dialog_type is M3UProviderDialog else "url"
    assert expected in dialog.status_label.value.casefold()


@pytest.mark.asyncio
async def test_provider_add_dialog_failure_stays_open_and_clears_secret() -> None:
    registration = FakeRegistration(RegisterXtreamProviderResponse(error="Unable to register"))
    dialog = XtreamProviderDialog(registration)  # type: ignore[arg-type]
    dialog.base_url_input.setText("https://server.example")
    dialog.username_input.setText("user")
    dialog.password_input.setText("secret")

    await dialog.submit()

    assert dialog.closed_successfully is False
    assert dialog.password_input.text() == ""
    assert "secret" not in dialog.status_label.value.casefold()


@pytest.mark.asyncio
async def test_m3u_duplicate_provider_feedback_stays_open_and_preserves_the_source() -> None:
    registration = FakeRegistration(
        RegisterXtreamProviderResponse(error="Provider ID is already registered")
    )
    dialog = M3UProviderDialog(registration)  # type: ignore[arg-type]
    dialog.source_input.setText("https://example.test/playlist.m3u")

    await dialog.submit()

    assert dialog.closed_successfully is False
    assert dialog.source_input.text() == "https://example.test/playlist.m3u"
    assert dialog.status_label.value == "This playlist has already been added"


def test_cancel_does_not_invoke_registration() -> None:
    registration = FakeRegistration()
    dialog = M3UProviderDialog(registration)  # type: ignore[arg-type]

    dialog.cancel_button.clicked.callbacks[0]()

    assert registration.requests == []
    assert dialog.cancelled is True


def test_m3u_dialog_browse_sets_a_file_uri_without_exposing_provider_fields() -> None:
    registration = FakeRegistration()
    dialog = M3UProviderDialog(registration)  # type: ignore[arg-type]
    FakeFileDialog.selected_path = "/var/playlists/playlist.m3u8"

    dialog._browse_local_file()

    assert dialog.source_input.text() == "file:///var/playlists/playlist.m3u8"
    assert dialog.provider_id_input.text() == ""
    assert dialog.status_label.value == "Local playlist selected"
