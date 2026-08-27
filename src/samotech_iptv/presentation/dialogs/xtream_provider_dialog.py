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
    RegisterXtreamProviderRequest,
    RegisterXtreamProviderResponse,
)
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.presentation.dialogs.provider_id import generated_provider_id
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from PySide6.QtWidgets import QWidget

    from samotech_iptv.application.use_cases.register_xtream_provider import (
        RegisterXtreamProvider,
    )

__all__ = ["XtreamProviderDialog"]


class XtreamProviderDialog(QDialog):
    """Collect ephemeral Xtream inputs and delegate secure registration to application."""

    def __init__(
        self,
        register_provider: RegisterXtreamProvider,
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
            "Use the server address supplied by your provider. Credentials are stored securely "
            "and are never shown after saving."
        )
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName("formHelp")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://provider.example:port")
        self.base_url_input.setAccessibleName("Xtream server URL")
        self.base_url_input.setToolTip("HTTP or HTTPS server URL, including a port when required")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Provider username")
        self.username_input.setAccessibleName("Xtream username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Provider password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setAccessibleName("Xtream password")
        self.password_input.setToolTip("Your provider password; it is cleared after submission")
        self.show_password = QCheckBox("Show password")
        self.show_password.setAccessibleName("Show Xtream password")
        self.show_password.toggled.connect(self._set_password_visible)
        self.save_button = QPushButton("Save provider")
        self.save_button.setObjectName("primary")
        self.save_button.setAccessibleName("Save Xtream provider")
        self.save_button.clicked.connect(self._schedule_submit)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setAccessibleName("Cancel Xtream provider setup")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel("Enter the provider details to continue")
        self.status_label.setObjectName("formStatus")
        self.status_label.setWordWrap(True)
        layout = QFormLayout(self)
        layout.addRow(self.help_label)
        layout.addRow("Server URL", self.base_url_input)
        layout.addRow("Username", self.username_input)
        layout.addRow("Password", self.password_input)
        layout.addRow("", self.show_password)
        layout.addRow(self.save_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add Xtream Provider")
        self.setMinimumWidth(440)
        apply_form_dialog_style(self)

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        create_owned_task(self, self.submit())

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit ephemeral fields, clearing the password without exposing it."""
        base_url = self.base_url_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not base_url or not username or not password:
            self.status_label.setText("Server URL, username, and password are required")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        try:
            URL(base_url)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Enter a valid HTTP or HTTPS server URL")
            return RegisterXtreamProviderResponse(error="Invalid server URL")
        self._set_busy(True)
        self.status_label.setText("Saving provider securely…")
        provider_id = generated_provider_id("xtream", base_url)
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
            self._set_busy(False)
            self.status_label.setText("Unable to register Xtream provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        self.password_input.clear()
        self._set_busy(False)
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to register Xtream provider")
            return response
        self.status_label.setText("Provider saved. Select it to load content.")
        if self._on_provider_added is not None:
            await self._on_provider_added(response.provider_id)
        self._close_after_success()
        return response

    def _set_password_visible(self, visible: bool) -> None:
        """Toggle password visibility only while this transient form is open."""
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )

    def _set_busy(self, busy: bool) -> None:
        """Prevent duplicate submissions while preserving the cancel affordance."""
        self.save_button.setEnabled(not busy)
        self.base_url_input.setEnabled(not busy)
        self.username_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.show_password.setEnabled(not busy)

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
