"""Presentation tests for credential-safe provider management dialogs."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos.provider import ProviderMetadata
from samotech_iptv.application.dtos.provider_registration import ProviderLifecycleResponse


class FakeSignal:
    """Minimal Qt signal double."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeDialog:
    """Minimal QDialog double."""

    def __init__(self) -> None:
        self.title = ""
        self.shown = False

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def setStyleSheet(self, _: str) -> None:  # noqa: N802
        pass

    def setMinimumWidth(self, _: int) -> None:  # noqa: N802
        pass

    def show(self) -> None:
        self.shown = True


class FakeFormLayout:
    """Minimal QFormLayout double."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double."""

    def __init__(self, value: str = "") -> None:
        self.value = value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def setWordWrap(self, _: bool) -> None:  # noqa: N802
        pass

    def setObjectName(self, _: str) -> None:  # noqa: N802
        pass


class FakeLineEdit:
    """Minimal QLineEdit double."""

    class EchoMode:
        """Minimal echo-mode namespace."""

        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.echo_mode: object | None = None

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, echo_mode: object) -> None:  # noqa: N802
        self.echo_mode = echo_mode

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def text(self) -> str:
        return self.value


class FakeComboBox:
    """Minimal QComboBox double with safe item-data selection semantics."""

    def __init__(self) -> None:
        self.items: list[tuple[str, object]] = []
        self.current_index = -1
        self.accessible_name = ""
        self.tooltip = ""
        self.signals_blocked = False

    def addItem(self, label: str, value: object) -> None:  # noqa: N802
        self.items.append((label, value))
        if self.current_index < 0:
            self.current_index = 0

    def blockSignals(self, blocked: bool) -> None:  # noqa: N802
        self.signals_blocked = blocked

    def clear(self) -> None:
        self.items.clear()
        self.current_index = -1

    def currentData(self) -> object:  # noqa: N802
        if not 0 <= self.current_index < len(self.items):
            return None
        return self.items[self.current_index][1]

    def findData(self, value: object) -> int:  # noqa: N802
        return next((index for index, item in enumerate(self.items) if item[1] == value), -1)

    def setAccessibleName(self, value: str) -> None:  # noqa: N802
        self.accessible_name = value

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        self.current_index = index

    def setToolTip(self, value: str) -> None:  # noqa: N802
        self.tooltip = value


class FakeButton:
    """Minimal QPushButton double."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()

    def setObjectName(self, _: str) -> None:  # noqa: N802
        pass

    def setToolTip(self, _: str) -> None:  # noqa: N802
        pass


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QComboBox = FakeComboBox
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.provider_edit_dialog import (  # noqa: E402
    ProviderEditDialog,
)
from samotech_iptv.presentation.dialogs.provider_list_dialog import (  # noqa: E402
    ProviderListDialog,
)


class FakeUpdateProvider:
    """Update use-case double recording only the ephemeral request object."""

    def __init__(self) -> None:
        self.request: object | None = None

    async def execute(self, request: object) -> ProviderLifecycleResponse:
        self.request = request
        return ProviderLifecycleResponse(provider_id="profile")


class FakeRemoveProvider:
    """Remove use-case double returning a generic safe outcome."""

    def __init__(self) -> None:
        self.provider_id: str | None = None

    async def execute(self, provider_id: str) -> ProviderLifecycleResponse:
        self.provider_id = provider_id
        return ProviderLifecycleResponse(provider_id=provider_id)


class FakeListProviders:
    """List use-case double backed by mutable safe provider summaries."""

    def __init__(self, providers: list[ProviderMetadata]) -> None:
        self.providers = providers

    async def execute(self) -> list[ProviderMetadata]:
        return self.providers


def _xtream_provider() -> ProviderMetadata:
    """Return a safe provider summary with no credential fields."""
    return ProviderMetadata(
        id="profile",
        name="profile",
        type="xtream",
        base_url="https://server.example.test",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_xtream_edit_keeps_credentials_blank_and_submits_only_optional_replacements() -> None:
    """Edit presentation never receives stored credentials or renders them to users."""
    update_provider = FakeUpdateProvider()
    dialog = ProviderEditDialog(_xtream_provider(), update_provider)  # type: ignore[arg-type]

    assert dialog.username_input.text() == ""
    assert dialog.password_input.text() == ""
    assert dialog.password_input.echo_mode is FakeLineEdit.EchoMode.Password
    assert dialog.save_button.clicked.callbacks == [dialog._schedule_submit]

    await dialog.submit()

    request = update_provider.request
    assert request is not None
    assert request.provider_id == "profile"
    assert request.base_url == "https://server.example.test"
    assert request.username is None
    assert request.password is None
    assert dialog.status_label.value == "Provider updated"
    assert "password" not in dialog.status_label.value.casefold()


def test_m3u_and_mag_edit_forms_only_offer_ephemeral_replacement_inputs() -> None:
    """M3U and MAG editors do not prefill protected source or device identity fields."""
    update_provider = FakeUpdateProvider()
    m3u_dialog = ProviderEditDialog(
        ProviderMetadata(
            id="playlist",
            name="playlist",
            type="m3u",
            base_url="https://safe.example.test/playlist.m3u",
            is_active=True,
        ),
        update_provider,  # type: ignore[arg-type]
    )
    mag_dialog = ProviderEditDialog(
        ProviderMetadata(
            id="portal",
            name="portal",
            type="mag",
            base_url="https://portal.example.test",
            is_active=True,
        ),
        update_provider,  # type: ignore[arg-type]
    )

    assert m3u_dialog.source_input.text() == ""
    assert mag_dialog.mac_address_input.text() == ""
    assert mag_dialog.mac_address_input.echo_mode is FakeLineEdit.EchoMode.Password


@pytest.mark.asyncio
async def test_provider_list_refreshes_safely_opens_edit_and_removes_selected_profile() -> None:
    """The provider list selects safe summaries and refreshes after generic removal feedback."""
    provider = _xtream_provider()
    list_providers = FakeListProviders([provider])
    update_provider = FakeUpdateProvider()
    remove_provider = FakeRemoveProvider()
    dialog = ProviderListDialog(
        list_providers,  # type: ignore[arg-type]
        update_provider,  # type: ignore[arg-type]
        remove_provider,  # type: ignore[arg-type]
    )

    await dialog.refresh()
    assert dialog.provider_selector.items == [
        ("Select a registered provider", ""),
        ("profile · xtream · Active", "profile"),
    ]
    assert dialog.provider_selector.accessible_name == "Registered provider"
    assert dialog._selected_provider() is None
    assert dialog.open_edit_dialog() is None
    assert dialog.status_label.value == "Select a registered provider"

    dialog.provider_selector.setCurrentIndex(1)
    edit_dialog = dialog.open_edit_dialog()

    assert edit_dialog is not None
    assert edit_dialog.shown
    assert dialog.provider_summary_label.value == "profile · xtream · Active"
    assert "server.example.test" not in dialog.provider_summary_label.value

    list_providers.providers = []
    await dialog.remove_selected()

    assert remove_provider.provider_id == "profile"
    assert dialog.status_label.value == "Provider removed"
    assert dialog.provider_summary_label.value == "No providers registered"
    assert dialog.provider_selector.items == [("Select a registered provider", "")]
    assert "profile" not in dialog.status_label.value


def test_provider_list_keeps_unavailable_capabilities_distinct_from_unsupported() -> None:
    from samotech_iptv.application.dtos.provider import (
        ProviderCapabilities,
        ProviderCapabilityState,
        ProviderCapabilityTruth,
        ProviderMetadata,
    )

    provider = ProviderMetadata(
        id="profile",
        name="profile",
        type="xtream",
        base_url="https://safe.example.test",
        is_active=True,
        capabilities=ProviderCapabilities(
            truth=ProviderCapabilityTruth(
                live_tv=ProviderCapabilityState.SUPPORTED,
                vod_movies=ProviderCapabilityState.NOT_SUPPORTED,
                vod_series=ProviderCapabilityState.NOT_AVAILABLE,
            )
        ),
    )

    summary = ProviderListDialog._format_provider(provider)

    assert "Live: supported" in summary
    assert "VOD: not supported" in summary
    assert "Series: not available" in summary
