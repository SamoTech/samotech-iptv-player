"""PySide6 dialog for safe provider-scoped Electronic Programme Guide display."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
)

from samotech_iptv.application.dtos import EPGEntryDTO, LoadEPGResponse, LoadRegisteredEPGRequest
from samotech_iptv.presentation.task_owner import create_owned_task

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG

__all__ = ["EPGGridDialog"]


class EPGGridDialog(QDialog):
    """Load and render safe EPG rows for a registered provider channel."""

    def __init__(
        self,
        load_registered_epg: LoadRegisteredEPG,
        provider_id: str | None = None,
        channel_id: str | None = None,
    ) -> None:
        super().__init__()
        self._load_registered_epg = load_registered_epg
        self._selected_provider_id = provider_id
        self._selected_channel_id = channel_id
        self.provider_id_input = QLineEdit()
        self.channel_id_input = QLineEdit()
        self.epg_list = QListWidget()
        self.load_epg_button = QPushButton("Load EPG")
        self.load_epg_button.clicked.connect(self._schedule_epg_load)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        if provider_id is None or channel_id is None:
            layout.addRow("Provider ID", self.provider_id_input)
            layout.addRow("Channel ID", self.channel_id_input)
        layout.addRow(self.load_epg_button)
        layout.addRow("Programme guide", self.epg_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Programme Guide")
        if provider_id is not None and channel_id is not None:
            self.status_label.setText("Ready to load the selected live channel guide")

    def _schedule_epg_load(self) -> None:
        """Queue EPG loading on the supported Qt-aware asynchronous event loop."""
        create_owned_task(self, self.load_epg())

    async def load_epg(self) -> LoadEPGResponse:
        """Load and display only title and schedule data for the selected channel."""
        provider_id = self._selected_provider_id or self.provider_id_input.text().strip()
        channel_id = self._selected_channel_id or self.channel_id_input.text().strip()
        if not provider_id or not channel_id:
            self._render_entries([])
            self.status_label.setText(
                "Select a live channel first, or enter a provider and channel ID in this "
                "advanced dialog"
            )
            return LoadEPGResponse(error="EPG selection required")
        try:
            response = await self._load_registered_epg.execute(
                LoadRegisteredEPGRequest(
                    provider_id=provider_id,
                    channel_id=channel_id,
                )
            )
        except Exception:  # noqa: BLE001
            self._render_entries([])
            self.status_label.setText(
                "Programme guide is unavailable. Check the selected channel and provider "
                "connection."
            )
            return LoadEPGResponse(error="Unable to load EPG")

        if response.error is not None:
            self._render_entries([])
            self.status_label.setText(
                "Programme guide is unavailable for the selected channel. Check provider "
                "access or try again."
            )
            return response

        self._render_entries(response.entries)
        self.status_label.setText(
            f"{len(response.entries)} programmes loaded"
            if response.entries
            else "No EPG entries found"
        )
        return response

    def _render_entries(self, entries: Sequence[EPGEntryDTO]) -> None:
        """Render only the EPG title and start/end times, never provider data or URLs."""
        self.epg_list.clear()
        for entry in entries:
            self.epg_list.addItem(f"{entry.start} – {entry.end} · {entry.title}")
