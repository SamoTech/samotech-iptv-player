from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
)

from samotech_iptv.application.dtos.history import LoadHistoryRequest

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.clear_history import ClearHistory
    from samotech_iptv.application.use_cases.load_history import LoadHistory

__all__ = ["HistoryLibraryDialog"]


class HistoryLibraryDialog(QDialog):  # type: ignore[misc]
    """Render recent history and support bounded clear-all behavior."""

    def __init__(self, load_history: LoadHistory, clear_history: ClearHistory) -> None:
        super().__init__()
        self._load_history = load_history
        self._clear_history = clear_history
        self.history_summary_label = QLabel()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._schedule_refresh)
        self.clear_button = QPushButton("Clear All History")
        self.clear_button.clicked.connect(self._schedule_clear_all)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.history_summary_label)
        layout.addRow(self.refresh_button)
        layout.addRow(self.clear_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("History")

    def _schedule_refresh(self) -> None:
        asyncio.create_task(self.refresh())

    async def refresh(self) -> None:
        """Reload recent history and render safe playback metadata."""
        try:
            response = await self._load_history.execute(LoadHistoryRequest())
        except Exception:  # noqa: BLE001
            self._show_error("Unable to load history")
            return
        if response.error:
            self._show_error(response.error)
            return
        self.history_summary_label.setText(
            "\n".join(
                f"{item.item_id} · {item.item_type} · watched {item.watched_at} · "
                f"position {item.position_seconds}s / duration {item.duration_seconds}s"
                for item in response.items
            )
            or "No viewing history"
        )
        self.status_label.setText("")

    def _schedule_clear_all(self) -> None:
        asyncio.create_task(self.clear_all())

    async def clear_all(self) -> None:
        """Confirm and clear all history; per-record deletion is intentionally absent."""
        confirmation = QMessageBox.question(
            self,
            "Clear History",
            "Clear all viewing history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        try:
            response = await self._clear_history.execute()
        except Exception:  # noqa: BLE001
            self._show_error("Unable to clear history")
            return
        if response.error:
            self._show_error(response.error)
            return
        self.status_label.setText(f"Cleared {response.cleared} history records")
        await self.refresh()

    def _show_error(self, message: str) -> None:
        self.status_label.setText(message or "Unable to load history")
