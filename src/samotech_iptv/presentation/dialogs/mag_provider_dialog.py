"""PySide6 manual MAG/Stalker provider-entry dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from samotech_iptv.application.dtos.provider_registration import (
    RegisterMAGProviderRequest,
    RegisterXtreamProviderResponse,
)

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider

__all__ = ["MAGProviderDialog"]


class MAGProviderDialog(QDialog):  # type: ignore[misc]
    """Collect authorized MAG/Stalker identity inputs for secure registration."""

    def __init__(self, register_provider: RegisterMAGProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.provider_id_input = QLineEdit()
        self.portal_url_input = QLineEdit()
        self.mac_address_input = QLineEdit()
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Portal URL", self.portal_url_input)
        layout.addRow("Device identity", self.mac_address_input)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add MAG/Stalker Provider")

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Submit transient identity input and clear it when registration finishes."""
        request = RegisterMAGProviderRequest(
            provider_id=self.provider_id_input.text(),
            portal_url=self.portal_url_input.text(),
            mac_address=self.mac_address_input.text(),
        )
        try:
            response = await self._register_provider.execute(request)
        finally:
            self.mac_address_input.clear()
        self.status_label.setText(
            "MAG/Stalker provider added"
            if response.provider_id is not None
            else response.error or "Registration failed"
        )
        return response
