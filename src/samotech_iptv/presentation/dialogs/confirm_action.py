"""Safe confirmation helpers for destructive presentation actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

__all__ = ["confirm_destructive_action"]


def confirm_destructive_action(parent: QWidget, title: str, message: str) -> bool:
    """Ask for explicit confirmation while keeping the safe default on No."""
    from PySide6.QtWidgets import QMessageBox

    response = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return response == QMessageBox.StandardButton.Yes
