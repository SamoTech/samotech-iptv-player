"""PySide6 manual Xtream provider-entry dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
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


class XtreamProviderDialog(QDialog):  # type: ignore[misc]
    """Collect ephemeral Xtream inputs and delegate secure registration to application."""

    def __init__(self, register_provider: RegisterXtreamProvider) -> None:
        super().__init__()
        self._register_provider = register_provider
        self.provider_id_input = QLineEdit()
        self.base_url_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Server URL", self.base_url_input)
        layout.addRow("Username", self.username_input)
        layout.addRow("Password", self.password_input)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add Xtream Provider")

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Submit ephemeral field values and clear the password from the dialog afterward."""
        request = RegisterXtreamProviderRequest(
            provider_id=self.provider_id_input.text(),
            base_url=self.base_url_input.text(),
            username=self.username_input.text(),
            password=self.password_input.text(),
        )
        try:
            response = await self._register_provider.execute(request)
        finally:
            self.password_input.clear()
        self.status_label.setText(
            "Xtream provider added"
            if response.provider_id is not None
            else response.error or "Registration failed"
        )
        return response
