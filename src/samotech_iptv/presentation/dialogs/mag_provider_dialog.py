from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from samotech_iptv.application.dtos.provider_registration import (
    RegisterMAGProviderRequest,
    RegisterXtreamProviderResponse,
)
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.presentation.dialogs.provider_id import generated_provider_id
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from PySide6.QtWidgets import QWidget

    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider

__all__ = ["MAGProviderDialog"]


class MAGProviderDialog(QDialog):
    """Collect authorized MAG/Stalker identity inputs for secure registration."""

    def __init__(
        self,
        register_provider: RegisterMAGProvider,
        on_provider_added: Callable[[str], Awaitable[None]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
        self._register_provider = register_provider
        self._on_provider_added = on_provider_added
        self.closed_successfully = False
        self.cancelled = False
        self.help_label = QLabel(
            "Use the portal URL and device identity supplied by an authorized provider. "
            "This client supports the provider's live-TV profile only."
        )
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName("formHelp")
        self.portal_url_input = QLineEdit()
        self.portal_url_input.setPlaceholderText("https://portal.example")
        self.portal_url_input.setAccessibleName("MAG or Stalker portal URL")
        self.portal_url_input.setToolTip("HTTP or HTTPS portal URL; do not include a device token")
        self.mac_address_input = QLineEdit()
        self.mac_address_input.setPlaceholderText("AA:BB:CC:DD:EE:FF")
        self.mac_address_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.mac_address_input.setAccessibleName("MAG or Stalker device identity")
        self.mac_address_input.setToolTip("Device identity is cleared after submission")
        self.show_identity = QCheckBox("Show device identity")
        self.show_identity.setAccessibleName("Show MAG or Stalker device identity")
        self.show_identity.toggled.connect(self._set_identity_visible)
        self.save_button = QPushButton("Save provider")
        self.save_button.setObjectName("primary")
        self.save_button.setAccessibleName("Save MAG or Stalker provider")
        self.save_button.clicked.connect(self._schedule_submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setAccessibleName("Cancel MAG or Stalker provider setup")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel("Enter the authorized portal details to continue")
        self.status_label.setObjectName("formStatus")
        self.status_label.setWordWrap(True)
        layout = QFormLayout(self)
        layout.addRow(self.help_label)
        layout.addRow("Portal URL", self.portal_url_input)
        layout.addRow("Device identity", self.mac_address_input)
        layout.addRow("", self.show_identity)
        layout.addRow(self.save_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add MAG/Stalker Provider")
        self.setMinimumWidth(440)
        apply_form_dialog_style(self)

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        create_owned_task(self, self.submit())

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit transient identity input without exposing the identity."""
        portal_url = self.portal_url_input.text().strip()
        mac_address = self.mac_address_input.text().strip()
        if not portal_url or not mac_address:
            self.status_label.setText("Portal URL and device identity are required")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        try:
            URL(portal_url)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Enter a valid HTTP or HTTPS portal URL")
            return RegisterXtreamProviderResponse(error="Invalid portal URL")
        self._set_busy(True)
        self.status_label.setText("Saving provider securely…")
        provider_id = generated_provider_id("mag", portal_url)
        request = RegisterMAGProviderRequest(
            provider_id=provider_id,
            portal_url=portal_url,
            mac_address=mac_address,
        )
        try:
            response = await self._register_provider.execute(request)
        except Exception:  # noqa: BLE001
            self.mac_address_input.clear()
            self._set_busy(False)
            self.status_label.setText("Unable to register MAG/Stalker provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        self.mac_address_input.clear()
        self._set_busy(False)
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to register MAG/Stalker provider")
            return response
        self.status_label.setText("Provider saved. Select it to load live TV.")
        if self._on_provider_added is not None:
            await self._on_provider_added(response.provider_id)
        self._close_after_success()
        return response

    def _set_identity_visible(self, visible: bool) -> None:
        """Toggle device identity visibility only while this transient form is open."""
        self.mac_address_input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )

    def _set_busy(self, busy: bool) -> None:
        """Prevent duplicate submissions while retaining secure field clearing."""
        self.portal_url_input.setEnabled(not busy)
        self.mac_address_input.setEnabled(not busy)
        self.show_identity.setEnabled(not busy)
        self.save_button.setEnabled(not busy)

    def _cancel(self) -> None:
        """Close without submitting any data."""
        reject = getattr(self, "reject", None)
        self.cancelled = True
        if reject is not None:
            reject()

    def _close_after_success(self) -> None:
        """Close after successful registration when running with a real QDialog."""
        self.closed_successfully = True
        accept = getattr(self, "accept", None)
        if accept is not None:
            accept()
