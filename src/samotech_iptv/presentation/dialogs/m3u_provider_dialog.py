from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from samotech_iptv.application.dtos.provider_registration import (
    RegisterM3UProviderRequest,
    RegisterXtreamProviderResponse,
)
from samotech_iptv.presentation.dialogs.provider_id import generated_provider_id
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from PySide6.QtWidgets import QWidget

    from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider

__all__ = ["M3UProviderDialog"]


class M3UProviderDialog(QDialog):
    """Collect an M3U source and delegate registration through the application boundary."""

    def __init__(
        self,
        register_provider: RegisterM3UProvider,
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
        self._loading = False
        self.provider_id_input = QLineEdit()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText(
            "https://example.org/playlist.m3u or a local M3U/M3U8 file"
        )
        self.source_input.setAccessibleName("M3U or M3U8 playlist source")
        self.source_input.setToolTip("Paste a playlist URL or choose an M3U/M3U8 file")
        self.browse_button = QPushButton("Browse Local File…")
        self.browse_button.setAccessibleName("Browse local M3U playlist")
        self.browse_button.clicked.connect(self._browse_local_file)
        self.load_button = QPushButton("Load Playlist")
        self.load_button.setAccessibleName("Load M3U playlist")
        self.load_button.clicked.connect(self._schedule_submit)
        self.save_button = self.load_button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setAccessibleName("Cancel M3U provider setup")
        self.cancel_button.clicked.connect(self._cancel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(QLabel("M3U / M3U8"))
        layout.addRow("Playlist URL", self.source_input)
        layout.addRow("or", self.browse_button)
        layout.addRow(self.load_button)
        layout.addRow(self.cancel_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Add M3U Provider")
        apply_form_dialog_style(self)

    def _schedule_submit(self) -> None:
        """Queue registration on the supported Qt-aware event loop."""
        if self._loading:
            return
        create_owned_task(self, self.submit())

    def _browse_local_file(self) -> None:
        """Select a local playlist without mixing it with provider-specific fields."""
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choose an M3U or M3U8 playlist",
            "",
            "IPTV playlists (*.m3u *.m3u8);;All files (*)",
        )
        if not selected:
            self.status_label.setText("No local playlist selected")
            return
        self.source_input.setText(Path(selected).resolve().as_uri())
        self.status_label.setText("Local playlist selected")

    @staticmethod
    def _generated_provider_id(source: str) -> str:
        """Derive a deterministic, non-secret identifier so M3U setup needs no extra field."""
        return generated_provider_id("m3u", source)

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        self.load_button.setEnabled(not loading)
        self.browse_button.setEnabled(not loading)
        self.cancel_button.setEnabled(not loading)

    async def submit(self) -> RegisterXtreamProviderResponse:
        """Validate and submit transient input, closing only after successful registration."""
        source = self.source_input.text().strip()
        if not source:
            self.status_label.setText("Enter a playlist URL or choose a local M3U/M3U8 file")
            return RegisterXtreamProviderResponse(error="Required fields are missing")
        provider_id = self.provider_id_input.text().strip() or self._generated_provider_id(source)
        request = RegisterM3UProviderRequest(provider_id=provider_id, source=source)
        self._set_loading(True)
        self.status_label.setText("Loading playlist…")
        try:
            response = await self._register_provider.execute(request)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Unable to register M3U provider")
            return RegisterXtreamProviderResponse(error="Unable to register provider")
        finally:
            self._set_loading(False)
        if response.provider_id is None:
            error = response.error or "Unable to register M3U provider"
            self.status_label.setText(
                "This playlist has already been added"
                if "already registered" in error.casefold()
                else error
            )
            return response
        self.source_input.clear()
        self.status_label.setText("M3U provider added")
        if self._on_provider_added is not None:
            await self._on_provider_added(response.provider_id)
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
