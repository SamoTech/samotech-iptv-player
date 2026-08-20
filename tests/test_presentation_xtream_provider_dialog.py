"""Tests for credential-safe PySide6 Xtream provider registration feedback."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


class FakeDialog:
    """Minimal QDialog double for provider-entry dialog tests."""

    def __init__(self) -> None:
        self.title: str | None = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title


class FakeFormLayout:
    """Minimal QFormLayout double that records the configured rows."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double that retains status copy."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeButton:
    """Minimal QPushButton double for dialog wiring."""

    def __init__(self, _: str) -> None:
        self.clicked = type("Signal", (), {"connect": lambda self, callback: None})()


class FakeLineEdit:
    """Minimal QLineEdit double for ephemeral credential collection."""

    class EchoMode:
        """Minimal echo-mode namespace."""

        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.echo_mode: object | None = None
        self.placeholder = ""
        self.accessible_name = ""

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, echo_mode: object) -> None:  # noqa: N802
        self.echo_mode = echo_mode

    def setPlaceholderText(self, placeholder: str) -> None:  # noqa: N802
        self.placeholder = placeholder

    def setAccessibleName(self, accessible_name: str) -> None:  # noqa: N802
        self.accessible_name = accessible_name

    def text(self) -> str:
        return self.value


class FakeRegistration:
    """Registration-use-case double with a controlled response."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.requests: list[object] = []

    async def execute(self, request: object) -> object:
        self.requests.append(request)
        return self.response


def _install_fake_pyside6() -> tuple[object | None, object | None]:
    original_pyside = sys.modules.get("PySide6")
    original_widgets = sys.modules.get("PySide6.QtWidgets")
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakeButton
    sys.modules.setdefault("PySide6", ModuleType("PySide6"))
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    return original_pyside, original_widgets


_original_pyside, _original_widgets = _install_fake_pyside6()

from samotech_iptv.application.dtos.provider_registration import (  # noqa: E402
    RegisterXtreamProviderResponse,
)
from samotech_iptv.presentation.dialogs.xtream_provider_dialog import (  # noqa: E402
    XtreamProviderDialog,
)

if _original_pyside is None:
    sys.modules.pop("PySide6", None)
else:
    sys.modules["PySide6"] = _original_pyside
if _original_widgets is None:
    sys.modules.pop("PySide6.QtWidgets", None)
else:
    sys.modules["PySide6.QtWidgets"] = _original_widgets


def _dialog(response: RegisterXtreamProviderResponse) -> XtreamProviderDialog:
    dialog = XtreamProviderDialog(FakeRegistration(response))  # type: ignore[arg-type]
    dialog.base_url_input.value = "https://iptv.example.test"
    dialog.username_input.value = "subscriber"
    dialog.password_input.value = "credential"  # noqa: S105
    return dialog


@pytest.mark.asyncio
async def test_submit_shows_success_status_and_clears_password() -> None:
    dialog = _dialog(RegisterXtreamProviderResponse(provider_id="home", error=None))

    response = await dialog.submit()

    assert response.provider_id == "home"
    assert dialog.status_label.value == "Xtream provider added"
    assert dialog.password_input.value == ""


@pytest.mark.asyncio
async def test_submit_shows_error_status_and_clears_password() -> None:
    dialog = _dialog(
        RegisterXtreamProviderResponse(provider_id=None, error="Server rejected credentials")
    )

    response = await dialog.submit()

    assert response.error == "Server rejected credentials"
    assert dialog.status_label.value == "Server rejected credentials"
    assert dialog.password_input.value == ""
