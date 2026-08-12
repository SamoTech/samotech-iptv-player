"""PySide6 manual M3U provider-entry dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from samotech_iptv.application.dtos.provider_registration import (
    RegisterM3UProviderRequest,
    RegisterXtreamProviderResponse,
)

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider

__all__ = ["M3UProviderDialog"]


class M3UProviderDialog(QDialog):  # type: ignore[misc]
    """Collect an M3U source and delegate registration through the application boundary."""

    def __init__(self, register_provider: RegisterM3UProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.provider_id_input = QLineEdit()
        self.source_input = QLineEdit()
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Playlist source", self.source_input)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add M3U Provider")

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Submit transient source input and clear it whenever registration finishes."""
        request = RegisterM3UProviderRequest(
            provider_id=self.provider_id_input.text(),
            source=self.source_input.text(),
        )
        try:
            response = await self._register_provider.execute(request)
        finally:
            self.source_input.clear()
        self.status_label.setText(
            "M3U provider added"
            if response.provider_id is not None
            else response.error or "Registration failed"
        )
        return response
