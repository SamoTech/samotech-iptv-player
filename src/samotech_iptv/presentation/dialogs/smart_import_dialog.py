"""Commercial Smart Import dialog for local IPTV configuration detection."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
)

from samotech_iptv.application.dtos.provider_registration import (
    RegisterM3UProviderRequest,
    RegisterMAGProviderRequest,
    RegisterXtreamProviderRequest,
)
from samotech_iptv.application.smart_import import (
    DetectedProviderInput,
    ImportProtocol,
    detect_provider_input,
    mask_mac,
    mask_password,
    suggest_provider_id,
)
from samotech_iptv.presentation.task_owner import create_owned_task

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider
    from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider
    from samotech_iptv.application.use_cases.register_xtream_provider import RegisterXtreamProvider

__all__ = ["SmartImportDialog"]

ProviderAddedCallback = Callable[[str], Awaitable[None]]


class SmartImportDialog(QDialog):
    """Detect and register IPTV input without exposing raw clipboard data externally."""

    def __init__(
        self,
        register_xtream_provider: RegisterXtreamProvider,
        register_m3u_provider: RegisterM3UProvider,
        register_mag_provider: RegisterMAGProvider,
        on_provider_added: ProviderAddedCallback | None = None,
    ) -> None:
        super().__init__()
        self._register_xtream_provider = register_xtream_provider
        self._register_m3u_provider = register_m3u_provider
        self._register_mag_provider = register_mag_provider
        self._on_provider_added = on_provider_added
        self._detected: DetectedProviderInput | None = None
        self._source_text = ""
        self.closed_successfully = False
        self.cancelled = False

        self.source_input = QPlainTextEdit()
        self.source_input.setPlaceholderText(
            "Paste IPTV data here. Xtream, M3U, and MAG/Stalker formats are detected locally."
        )
        self.source_input.setAccessibleName("IPTV provider information")
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.detect_button = QPushButton("Detect & Continue")
        self.detect_button.clicked.connect(self._detect)
        self.protocol_selector = QComboBox()
        self.protocol_selector.addItem("Select detected protocol", None)
        self.protocol_selector.currentIndexChanged.connect(self._protocol_selection_changed)
        self.protocol_selector.setEnabled(False)

        self.provider_id_input = QLineEdit()
        self.provider_id_input.setPlaceholderText("Generated from safe provider details")
        self.server_input = QLineEdit()
        self.portal_input = QLineEdit()
        self.playlist_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.mac_input = QLineEdit()
        self.mac_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.preview_label = QLabel("No provider detected")
        self.status_label = QLabel()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        self.test_button.setEnabled(False)
        self.add_button = QPushButton("Add Provider")
        self.add_button.clicked.connect(self._schedule_submit)
        self.add_button.setEnabled(False)
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._cancel)

        layout = QFormLayout(self)
        layout.addRow(QLabel("SMART IMPORT"))
        layout.addRow("Provider information", self.source_input)
        layout.addRow(self.paste_button)
        layout.addRow(self.detect_button)
        layout.addRow("Detected protocol", self.protocol_selector)
        layout.addRow("Preview", self.preview_label)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Server URL", self.server_input)
        layout.addRow("Portal URL", self.portal_input)
        layout.addRow("Playlist URL", self.playlist_input)
        layout.addRow("Username", self.username_input)
        layout.addRow("Password", self.password_input)
        layout.addRow("MAC address", self.mac_input)
        layout.addRow(self.test_button)
        layout.addRow(self.add_button)
        layout.addRow(self.back_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add IPTV Provider — Smart Import")

    def paste_from_clipboard(self) -> None:
        """Read clipboard text locally without logging or sending its contents elsewhere."""
        clipboard = QApplication.clipboard()
        self.source_input.setPlainText(clipboard.text())
        self.status_label.setText("Clipboard content loaded locally")

    def _detect(self) -> None:
        """Detect the current text and render a safe preview."""
        self._source_text = self.source_input.toPlainText()
        self._detected = detect_provider_input(self._source_text)
        self._render_detection(self._detected)

    def _render_detection(self, detected: DetectedProviderInput) -> None:
        self.protocol_selector.blockSignals(True)
        self.protocol_selector.clear()
        self.protocol_selector.addItem("Select detected protocol", None)
        if detected.protocol is ImportProtocol.AMBIGUOUS:
            for candidate in detected.candidates:
                self.protocol_selector.addItem(candidate.value.upper(), candidate)
            self.protocol_selector.setEnabled(True)
        else:
            self.protocol_selector.addItem(detected.protocol.value.upper(), detected.protocol)
            self.protocol_selector.setCurrentIndex(1)
            self.protocol_selector.setEnabled(False)
        self.protocol_selector.blockSignals(False)
        self._populate_fields(detected)

    def _protocol_selection_changed(self, _: int) -> None:
        """Resolve an explicitly selected ambiguous protocol through the same local parser."""
        selected = self.protocol_selector.currentData()
        if not isinstance(selected, ImportProtocol) or selected is ImportProtocol.AMBIGUOUS:
            self._populate_fields(self._detected)
            return
        marker = {
            ImportProtocol.XTREAM: "Xtream:",
            ImportProtocol.M3U: "M3U:",
            ImportProtocol.MAG: "MAG:",
        }[selected]
        self._detected = detect_provider_input(f"{marker}\n{self._source_text}")
        self._populate_fields(self._detected)

    def _populate_fields(self, detected: DetectedProviderInput | None) -> None:
        """Populate only safe preview values and clear unavailable protocol fields."""
        if detected is None:
            return
        self.server_input.setText(detected.server_url or "")
        self.portal_input.setText(detected.portal_url or "")
        self.playlist_input.setText(detected.playlist_url or "")
        self.username_input.setText(detected.username or "")
        self.password_input.setText(detected.password or "")
        self.mac_input.setText(detected.mac_address or "")
        self.provider_id_input.setText(
            suggest_provider_id(detected) if detected.protocol != ImportProtocol.AMBIGUOUS else ""
        )
        if detected.protocol is ImportProtocol.XTREAM:
            details = (
                f"Xtream · Server {detected.server_url or 'not detected'} · "
                f"Password {mask_password(detected.password)}"
            )
        elif detected.protocol is ImportProtocol.M3U:
            details = (
                f"M3U · Playlist {detected.playlist_url or 'content detected; URL required to add'}"
            )
        elif detected.protocol is ImportProtocol.MAG:
            details = (
                f"MAG / Stalker · Portal {detected.portal_url or 'not detected'} · "
                f"MAC {mask_mac(detected.mac_address)}"
            )
        elif detected.protocol is ImportProtocol.AMBIGUOUS:
            details = "More than one possible provider format was found. Select one above."
        else:
            details = "No supported IPTV format detected."
        missing = "; ".join(detected.missing_required_fields)
        warning = f" Missing: {missing}." if missing else " Required information detected."
        self.preview_label.setText(details + warning)
        self.status_label.setText("; ".join(detected.warnings) if detected.warnings else "")
        complete = detected.is_complete and detected.protocol is not ImportProtocol.AMBIGUOUS
        self.add_button.setEnabled(complete)
        self.test_button.setEnabled(complete)
        if detected.protocol is ImportProtocol.M3U and detected.playlist_url is None:
            self.add_button.setEnabled(False)
            self.test_button.setEnabled(False)

    def _test_connection(self) -> None:
        """Report validation without claiming an unimplemented network operation."""
        if self._detected is None or not self._detected.is_complete:
            self.status_label.setText("Complete the detected required fields first")
            return
        self.status_label.setText(
            "Validation passed; add the provider to use its existing connection workflow"
        )

    def _schedule_submit(self) -> None:
        create_owned_task(self, self.submit())

    async def submit(self) -> None:
        """Submit normalized fields through the existing canonical registration use case."""
        detected = self._detected
        if detected is None or not detected.is_complete:
            self.status_label.setText("Detect a complete provider configuration first")
            return
        provider_id = self.provider_id_input.text().strip()
        if not provider_id:
            self.status_label.setText("Provider ID is required")
            return
        if detected.protocol is ImportProtocol.XTREAM:
            xtream_request = RegisterXtreamProviderRequest(
                provider_id=provider_id,
                base_url=self.server_input.text().strip(),
                username=self.username_input.text().strip(),
                password=self.password_input.text(),
            )
            response = await self._register_xtream_provider.execute(xtream_request)
        elif detected.protocol is ImportProtocol.M3U:
            m3u_request = RegisterM3UProviderRequest(
                provider_id=provider_id,
                source=self.playlist_input.text().strip(),
            )
            response = await self._register_m3u_provider.execute(m3u_request)
        else:
            mag_request = RegisterMAGProviderRequest(
                provider_id=provider_id,
                portal_url=self.portal_input.text().strip(),
                mac_address=self.mac_input.text(),
            )
            response = await self._register_mag_provider.execute(mag_request)
        self.password_input.clear()
        self.mac_input.clear()
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to add provider")
            return
        self.source_input.clear()
        self.closed_successfully = True
        self.status_label.setText("Provider added")
        if self._on_provider_added is not None:
            await self._on_provider_added(response.provider_id)
        accept = getattr(self, "accept", None)
        if callable(accept):
            accept()

    def _cancel(self) -> None:
        self.cancelled = True
        reject = getattr(self, "reject", None)
        if callable(reject):
            reject()
