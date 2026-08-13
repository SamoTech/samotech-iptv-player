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
    def __init__(self) -> None:
        self.value = ""

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


class FakeButton:
    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()


widgets = ModuleType("PySide6.QtWidgets")
widgets.QDialog = FakeDialog
widgets.QFormLayout = FakeFormLayout
widgets.QLabel = FakeLabel
widgets.QLineEdit = FakeLineEdit
widgets.QPushButton = FakeButton
sys.modules["PySide6"] = ModuleType("PySide6")
sys.modules["PySide6.QtWidgets"] = widgets

from samotech_iptv.presentation.dialogs.m3u_provider_dialog import M3UProviderDialog  # noqa: E402
from samotech_iptv.presentation.dialogs.mag_provider_dialog import MAGProviderDialog  # noqa: E402
from samotech_iptv.presentation.dialogs.xtream_provider_dialog import (  # noqa: E402
    XtreamProviderDialog,
)


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
        (M3UProviderDialog, {"provider_id_input": "m3u", "source_input": "file:///playlist.m3u"}),
        (
            XtreamProviderDialog,
            {
                "provider_id_input": "xtream",
                "base_url_input": "https://server.example",
                "username_input": "user",
                "password_input": "secret",
            },
        ),
        (
            MAGProviderDialog,
            {
                "provider_id_input": "mag",
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

    assert dialog.save_button.text == "Save"
    assert dialog.cancel_button.text == "Cancel"
    assert dialog.cancel_button.clicked.callbacks == [dialog._cancel]
    for field_name, value in values.items():
        getattr(dialog, field_name).setText(value)

    await dialog.submit()

    assert len(registration.requests) == 1
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
    assert "required" in dialog.status_label.value.casefold()


@pytest.mark.asyncio
async def test_provider_add_dialog_failure_stays_open_and_clears_secret() -> None:
    registration = FakeRegistration(RegisterXtreamProviderResponse(error="Unable to register"))
    dialog = XtreamProviderDialog(registration)  # type: ignore[arg-type]
    dialog.provider_id_input.setText("xtream")
    dialog.base_url_input.setText("https://server.example")
    dialog.username_input.setText("user")
    dialog.password_input.setText("secret")

    await dialog.submit()

    assert dialog.closed_successfully is False
    assert dialog.password_input.text() == ""
    assert "secret" not in dialog.status_label.value.casefold()


def test_cancel_does_not_invoke_registration() -> None:
    registration = FakeRegistration()
    dialog = M3UProviderDialog(registration)  # type: ignore[arg-type]

    dialog.cancel_button.clicked.callbacks[0]()

    assert registration.requests == []
    assert dialog.cancelled is True
