"""Credential-safe, type-aware provider edit dialog."""

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

from samotech_iptv.application.dtos.provider_registration import UpdateProviderRequest

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider import ProviderMetadata
    from samotech_iptv.application.use_cases.provider_lifecycle import UpdateProvider

__all__ = ["ProviderEditDialog"]


class ProviderEditDialog(QDialog):
    """Edit safe metadata and optional credentials for one registered provider.

    Passwords, MAC addresses, and protected playlist URLs are never read back into
    presentation. A blank optional credential field explicitly means "keep existing".
    """

    def __init__(self, provider: ProviderMetadata, update_provider: UpdateProvider) -> None:
        super().__init__()
        self._provider = provider
        self._update_provider = update_provider
        self.provider_id_label = QLabel(provider.id)
        self.status_label = QLabel()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._schedule_submit)
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_label)
        layout.addRow("Provider type", QLabel(provider.type))
        self._add_type_specific_fields(layout)
        layout.addRow(self.save_button)
        layout.addRow(self.status_label)
        self.setWindowTitle(f"Edit {provider.type} Provider")

    def _add_type_specific_fields(self, layout: QFormLayout) -> None:
        """Render only fields that are safe and applicable to this provider type."""
        if self._provider.type == "m3u":
            self.source_input = QLineEdit()
            layout.addRow("New source", self.source_input)
            layout.addRow("Current safe source", QLabel(self._provider.base_url))
            return
        self.base_url_input = QLineEdit()
        self.base_url_input.setText(self._provider.base_url)
        layout.addRow("Server URL", self.base_url_input)
        if self._provider.type == "xtream":
            self.username_input = QLineEdit()
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("New username", self.username_input)
            layout.addRow("New password", self.password_input)
            return
        self.mac_address_input = QLineEdit()
        self.mac_address_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("New MAC address", self.mac_address_input)

    def _schedule_submit(self) -> None:
        """Queue the asynchronous update on the supported Qt-aware event loop."""
        asyncio.create_task(self.submit())

    async def submit(self) -> None:
        """Submit safe field changes and clear credential input regardless of outcome."""
        request = self._request_from_inputs()
        try:
            response = await self._update_provider.execute(request)
        finally:
            self._clear_optional_credential_inputs()
        self.status_label.setText(
            "Provider updated"
            if response.provider_id is not None
            else response.error or "Unable to update provider"
        )

    def _request_from_inputs(self) -> UpdateProviderRequest:
        """Translate only currently entered values to an ephemeral update request."""
        if self._provider.type == "m3u":
            return UpdateProviderRequest(
                provider_id=self._provider.id,
                source=self._optional_text(self.source_input),
            )
        if self._provider.type == "xtream":
            return UpdateProviderRequest(
                provider_id=self._provider.id,
                base_url=self._optional_text(self.base_url_input),
                username=self._optional_text(self.username_input),
                password=self._optional_text(self.password_input),
            )
        return UpdateProviderRequest(
            provider_id=self._provider.id,
            base_url=self._optional_text(self.base_url_input),
            mac_address=self._optional_text(self.mac_address_input),
        )

    def _clear_optional_credential_inputs(self) -> None:
        """Clear temporary credential fields without ever displaying their contents."""
        if self._provider.type == "xtream":
            self.username_input.clear()
            self.password_input.clear()
        elif self._provider.type == "mag":
            self.mac_address_input.clear()
        elif self._provider.type == "m3u":
            self.source_input.clear()

    @staticmethod
    def _optional_text(field: QLineEdit) -> str | None:
        """Return a trimmed non-empty value, preserving blank fields as no change."""
        value = field.text().strip()
        return value or None
