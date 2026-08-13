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
    RegisterXtreamProviderRequest,
    RegisterXtreamProviderResponse,
)

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )

__all__ = ["XtreamProviderDialog"]


class XtreamProviderDialog(QDialog):
    """Collect ephemeral Xtream inputs and delegate secure registration to application."""

    def __init__(self, register_provider: RegisterXtreamProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.closed_successfully = False
        self.cancelled = False
        self.provider_id_input = QLineEdit()
        self.base_url_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._schedule_submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Server URL", self.base_url_input)
        layout.addRow("Username", self.username_input)
        layout.addRow("Password", self.password_input)
        layout.addRow(self.save_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add Xtream Provider")

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        asyncio.create_task(self.submit())

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit ephemeral fields, clearing the password without exposing it."""
        provider_id = self.provider_id_input.text().strip()
        base_url = self.base_url_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not provider_id or not base_url or not username or not password:
            self.status_label.setText("All Xtream fields are required")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        request = RegisterXtreamProviderRequest(
            provider_id=provider_id,
            base_url=base_url,
            username=username,
            password=password,
        )
        try:
            response = await self._register_provider.execute(request)
        except Exception:  # noqa: BLE001
            self.password_input.clear()
            self.status_label.setText("Unable to register Xtream provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        self.password_input.clear()
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to register Xtream provider")
            return response
        self.status_label.setText("Xtream provider added")
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
