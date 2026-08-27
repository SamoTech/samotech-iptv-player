"""Qt dialog for safe persisted playback-history browsing and clearing."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
)

from samotech_iptv.application.dtos import LoadHistoryRequest
from samotech_iptv.presentation.dialogs.confirm_action import confirm_destructive_action
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from samotech_iptv.application.dtos import HistoryItemDTO
    from samotech_iptv.application.use_cases.clear_history import ClearHistory
    from samotech_iptv.application.use_cases.load_history import LoadHistory

__all__ = ["HistoryLibraryDialog"]

_LOAD_ERROR = "Unable to load history"
_CLEAR_ERROR = "Unable to clear history"


class HistoryLibraryDialog(QDialog):
    """Render safe history summaries and offer only the existing clear-all operation."""

    def __init__(self, load_history: LoadHistory, clear_history: ClearHistory) -> None:
        super().__init__()
        self._load_history = load_history
        self._clear_history = clear_history
        self.history_summary_label = QLabel()
        self.refresh_button = QPushButton("Refresh History")
        self.refresh_button.setAccessibleName("Refresh playback history")
        self.refresh_button.setToolTip("Reload saved playback history")
        self.refresh_button.clicked.connect(self._schedule_refresh)
        self.clear_button = QPushButton("Clear History")
        self.clear_button.setObjectName("destructive")
        self.clear_button.setAccessibleName("Clear playback history")
        self.clear_button.setToolTip("Permanently clear all saved playback history")
        self.clear_button.clicked.connect(self._schedule_clear)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.history_summary_label)
        layout.addRow(self.refresh_button)
        layout.addRow(self.clear_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("History")
        apply_form_dialog_style(self)

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
        if not confirm_destructive_action(
            self,
            "Clear playback history?",
            "This permanently removes all saved playback history. Continue?",
        ):
            self.status_label.setText("History clear canceled")
            return
        response = await self._clear_history.execute()
        if response.error is not None:
            self.status_label.setText(_CLEAR_ERROR)
            return
        self.status_label.setText(f"Cleared {response.cleared} history entries")
        await self.refresh()

    @staticmethod
    def _format_history_item(item: HistoryItemDTO) -> str:
        """Render safe, user-oriented progress without internal item identifiers."""
        item_type = item.item_type.replace("_", " ").title()
        if item.completed:
            progress = "Completed"
        elif item.duration_seconds > 0:
            progress = (
                f"Continue at {HistoryLibraryDialog._format_duration(item.position_seconds)} "
                f"of {HistoryLibraryDialog._format_duration(item.duration_seconds)}"
            )
        else:
            progress = "Watched live"
        watched_at = HistoryLibraryDialog._format_watched_at(item.watched_at)
        return f"{item_type} · {progress} · Last watched {watched_at}"

    @staticmethod
    def _format_duration(seconds: int) -> str:
        minutes, remainder = divmod(max(0, seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{remainder:02d}" if hours else f"{minutes}:{remainder:02d}"

    @staticmethod
    def _format_watched_at(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return "recently"

    def _schedule_refresh(self) -> None:
        """Queue history refresh on the supported Qt-aware event loop."""
        create_owned_task(self, self.refresh())

    def _schedule_clear(self) -> None:
        """Queue clear-all on the supported Qt-aware event loop."""
        create_owned_task(self, self.clear())
