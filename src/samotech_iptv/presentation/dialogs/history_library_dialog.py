"""Qt dialog for safe persisted playback-history browsing and clearing."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
)

from samotech_iptv.application.dtos import LoadHistoryRequest

if TYPE_CHECKING:
    from samotech_iptv.application.dtos import HistoryItemDTO
    from samotech_iptv.application.use_cases.clear_history import ClearHistory
    from samotech_iptv.application.use_cases.load_history import LoadHistory

__all__ = ["HistoryLibraryDialog"]

_LOAD_ERROR = "Unable to load history"
_CLEAR_ERROR = "Unable to clear history"


class HistoryLibraryDialog(QDialog):  # type: ignore[misc]
    """Render safe history summaries and offer only the existing clear-all operation."""

    def __init__(self, load_history: LoadHistory, clear_history: ClearHistory) -> None:
        super().__init__()
        self._load_history = load_history
        self._clear_history = clear_history
        self.history_summary_label = QLabel()
        self.refresh_button = QPushButton("Refresh History")
        self.refresh_button.clicked.connect(self._schedule_refresh)
        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self._schedule_clear)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.history_summary_label)
        layout.addRow(self.refresh_button)
        layout.addRow(self.clear_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("History")

    async def refresh(self) -> None:
        """Refresh presentation-safe history records through the application boundary."""
        response = await self._load_history.execute(LoadHistoryRequest())
        if response.error is not None:
            self.history_summary_label.setText("No history available")
            self.status_label.setText(_LOAD_ERROR)
            return
        self.history_summary_label.setText(
            "\n".join(self._format_history_item(item) for item in response.items)
            or "No history recorded"
        )
        self.status_label.setText("" if response.items else "No history recorded")

    async def clear(self) -> None:
        """Clear all history only through the existing safe clear-all use case."""
        response = await self._clear_history.execute()
        if response.error is not None:
            self.status_label.setText(_CLEAR_ERROR)
            return
        self.status_label.setText(f"Cleared {response.cleared} history entries")
        await self.refresh()

    @staticmethod
    def _format_history_item(item: HistoryItemDTO) -> str:
        """Render canonical identity, watched time, and the existing stored progress values."""
        progress = (
            f"{item.position_seconds}s / {item.duration_seconds}s"
            if item.duration_seconds > 0
            else f"{item.position_seconds}s"
        )
        return f"{item.id} · {item.item_type} · {item.item_id} · {progress} · {item.watched_at}"

    def _schedule_refresh(self) -> None:
        """Queue history refresh on the supported Qt-aware event loop."""
        asyncio.create_task(self.refresh())

    def _schedule_clear(self) -> None:
        """Queue clear-all on the supported Qt-aware event loop."""
        asyncio.create_task(self.clear())
