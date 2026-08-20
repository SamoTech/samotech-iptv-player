"""Qt dialog for a user-copyable, sanitized playback diagnostic report."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

__all__ = ["PlaybackDiagnosticsDialog"]

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class PlaybackDiagnosticsDialog(QDialog):
    """Display a pre-sanitized diagnostic report without retaining any sensitive input."""

    def __init__(self, report: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report = report
        self.setWindowTitle("Playback Diagnostics")
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Safe to copy into a bug report. Credentials and private URLs are excluded.")
        )
        self.report_view = QPlainTextEdit(report)
        self.report_view.setReadOnly(True)
        self.report_view.setAccessibleName("Safe playback diagnostic report")
        layout.addWidget(self.report_view)
        self.copy_button = QPushButton("Copy Diagnostic Report")
        self.copy_button.setAccessibleName("Copy safe playback diagnostic report")
        self.copy_button.clicked.connect(self.copy_report)
        layout.addWidget(self.copy_button)
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def copy_report(self) -> None:
        """Copy only the pre-sanitized report to the local clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._report)
        self.status_label.setText("Safe diagnostic report copied")
