from __future__ import annotations

import asyncio
import importlib
import sys

widgets_module = sys.modules.get("PySide6.QtWidgets")
if widgets_module is not None and not hasattr(widgets_module, "QApplication"):
    sys.modules.pop("PySide6.QtWidgets", None)
    sys.modules.pop("PySide6", None)
importlib.import_module("PySide6")
importlib.import_module("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication  # noqa: E402

from samotech_iptv.application.dtos.provider_registration import (  # noqa: E402
    RegisterXtreamProviderResponse,
)
from samotech_iptv.presentation.dialogs.smart_import_dialog import SmartImportDialog  # noqa: E402


class FakeRegistration:
    def __init__(self) -> None:
        self.requests: list[object] = []

    async def execute(self, request: object) -> RegisterXtreamProviderResponse:
        self.requests.append(request)
        return RegisterXtreamProviderResponse(provider_id="saved-provider")


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_smart_import_clipboard_preview_and_registration_are_local_and_masked() -> None:
    _app()
    xtream = FakeRegistration()
    m3u = FakeRegistration()
    mag = FakeRegistration()
    added: list[str] = []

    async def on_added(provider_id: str) -> None:
        added.append(provider_id)

    dialog = SmartImportDialog(xtream, m3u, mag, on_added)
    clipboard = QApplication.clipboard()
    clipboard.setText(
        "Xtream URL: https://stream.example:8080/get.php?username=user&password=secret"
    )
    dialog.paste_from_clipboard()
    assert "secret" in dialog.source_input.toPlainText()
    dialog._detect()

    assert dialog._detected is not None
    assert dialog._detected.protocol.value == "xtream"
    assert "secret" not in dialog.preview_label.text()
    assert "••••••••" in dialog.preview_label.text()
    assert dialog.add_button.isEnabled()

    asyncio.run(dialog.submit())

    assert len(xtream.requests) == 1
    assert m3u.requests == []
    assert mag.requests == []
    assert added == ["saved-provider"]
    assert dialog.password_input.text() == ""
    assert dialog.source_input.toPlainText() == ""
    assert dialog.closed_successfully is True


def test_smart_import_minimally_requests_missing_password() -> None:
    _app()
    registration = FakeRegistration()
    dialog = SmartImportDialog(registration, FakeRegistration(), FakeRegistration())
    dialog.source_input.setPlainText("Server: https://stream.example:8080\nUsername: user")
    dialog._detect()

    assert dialog._detected is not None
    assert dialog._detected.missing_required_fields == ("password",)
    assert not dialog.add_button.isEnabled()
    assert "Password is required." in dialog.status_label.text()


class FakeSelector:
    def __init__(self) -> None:
        self.selected: int | None = None

    def findData(self, provider_id: str) -> int:  # noqa: N802
        return 3 if provider_id == "saved-provider" else -1

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        self.selected = index


class FakeShell:
    def __init__(self) -> None:
        self.provider_selector = FakeSelector()
        self.refreshed = False

    async def refresh_providers(self) -> None:
        self.refreshed = True


class FakeProviderList:
    def __init__(self) -> None:
        self.refreshed = False

    async def refresh(self) -> None:
        self.refreshed = True


class FakeStatusBar:
    def __init__(self) -> None:
        self.message = ""

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.message = message


def test_provider_added_refreshes_selector_and_provider_list_without_restart() -> None:
    from samotech_iptv.presentation.views.main_window import MainWindow

    class WindowFake:
        def __init__(self) -> None:
            self.player_shell = FakeShell()
            self._active_provider_list_dialog = FakeProviderList()
            self.status_bar = FakeStatusBar()

        def statusBar(self) -> FakeStatusBar:  # noqa: N802
            return self.status_bar

    window = WindowFake()

    asyncio.run(MainWindow._provider_added(window, "saved-provider"))

    assert window.player_shell.refreshed is True
    assert window.player_shell.provider_selector.selected == 3
    assert window._active_provider_list_dialog.refreshed is True
    assert window.status_bar.message == "Provider added and available immediately"
