from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
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

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider

__all__ = ["MAGProviderDialog"]


class MAGProviderDialog(QDialog):
    """Collect authorized MAG/Stalker identity inputs for secure registration."""

    def __init__(self, register_provider: RegisterMAGProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.closed_successfully = False
        self.cancelled = False
        self.provider_id_input = QLineEdit()
        self.portal_url_input = QLineEdit()
        self.mac_address_input = QLineEdit()
        self.mac_address_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._schedule_submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Portal URL", self.portal_url_input)
        layout.addRow("Device identity", self.mac_address_input)
        layout.addRow(self.save_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add MAG/Stalker Provider")

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        asyncio.create_task(self.submit())

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit transient identity input without exposing the identity."""
        provider_id = self.provider_id_input.text().strip()
        portal_url = self.portal_url_input.text().strip()
        mac_address = self.mac_address_input.text().strip()
        if not provider_id or not portal_url or not mac_address:
            self.status_label.setText("Provider ID, portal URL, and device identity are required")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        request = RegisterMAGProviderRequest(
            provider_id=provider_id,
            portal_url=portal_url,
            mac_address=mac_address,
        )
        try:
            response = await self._register_provider.execute(request)
        except Exception:  # noqa: BLE001
            self.mac_address_input.clear()
            self.status_label.setText("Unable to register MAG/Stalker provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        self.mac_address_input.clear()
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to register MAG/Stalker provider")
            return response
        self.status_label.setText("MAG/Stalker provider added")
        self._close_after_success()
        return response

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
