"""PySide6 dialog for safe provider-scoped Electronic Programme Guide display."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
)

from samotech_iptv.application.dtos import EPGEntryDTO, LoadEPGResponse, LoadRegisteredEPGRequest

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG

__all__ = ["EPGGridDialog"]


class EPGGridDialog(QDialog):  # type: ignore[misc]
    """Load and render safe EPG rows for a registered provider channel."""

    def __init__(self, load_registered_epg: LoadRegisteredEPG) -> None:
        super().__init__()
        self._load_registered_epg = load_registered_epg
        self.provider_id_input = QLineEdit()
        self.channel_id_input = QLineEdit()
        self.epg_list = QListWidget()
        self.load_epg_button = QPushButton("Load EPG")
        self.load_epg_button.clicked.connect(self._schedule_epg_load)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Channel ID", self.channel_id_input)
        layout.addRow(self.load_epg_button)
        layout.addRow("Programme guide", self.epg_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Programme Guide")

    def _schedule_epg_load(self) -> None:
        """Queue EPG loading on the supported Qt-aware asynchronous event loop."""
        asyncio.create_task(self.load_epg())

    async def load_epg(self) -> LoadEPGResponse:
        """Load and display only title and schedule data for the selected channel."""
        try:
            response = await self._load_registered_epg.execute(
                LoadRegisteredEPGRequest(
                    provider_id=self.provider_id_input.text(),
                    channel_id=self.channel_id_input.text(),
                )
            )
        except Exception:  # noqa: BLE001
            self._render_entries([])
            self.status_label.setText("Unable to load EPG")
            return LoadEPGResponse(error="Unable to load EPG")

        if response.error is not None:
            self._render_entries([])
            self.status_label.setText("Unable to load EPG")
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
