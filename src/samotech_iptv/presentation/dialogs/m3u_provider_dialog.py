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
    RegisterM3UProviderRequest,
    RegisterXtreamProviderResponse,
)

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider

__all__ = ["M3UProviderDialog"]


class M3UProviderDialog(QDialog):
    """Collect an M3U source and delegate registration through the application boundary."""

    def __init__(self, register_provider: RegisterM3UProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.closed_successfully = False
        self.cancelled = False
        self.provider_id_input = QLineEdit()
        self.source_input = QLineEdit()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._schedule_submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Playlist source", self.source_input)
        layout.addRow(self.save_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add M3U Provider")

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        asyncio.create_task(self.submit())

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit transient input, closing only after successful registration."""
        provider_id = self.provider_id_input.text().strip()
        source = self.source_input.text().strip()
        if not provider_id or not source:
            self.status_label.setText("Provider ID and playlist source are required")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        request = RegisterM3UProviderRequest(provider_id=provider_id, source=source)
        try:
            response = await self._register_provider.execute(request)
        except Exception:  # noqa: BLE001
            self.source_input.clear()
            self.status_label.setText("Unable to register M3U provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        self.source_input.clear()
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to register M3U provider")
            return response
        self.status_label.setText("M3U provider added")
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
