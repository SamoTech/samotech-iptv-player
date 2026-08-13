"""Qt dialog for saving the non-secret desktop theme preference."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
    from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference

__all__ = ["ThemeSettingsDialog"]


class ThemeSettingsDialog(QDialog):
    """Edit one of the supported system, light, or dark desktop preferences."""

    def __init__(
        self, load_theme_preference: LoadThemePreference, save_theme_preference: SaveThemePreference
    ) -> None:
        super().__init__()
        self._load_theme_preference = load_theme_preference
        self._save_theme_preference = save_theme_preference
        self.preference_input = QLineEdit()
        self.save_button = QPushButton("Save Theme")
        self.save_button.clicked.connect(self._schedule_save)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Theme (system, light, or dark)", self.preference_input)
        layout.addRow(self.save_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Settings")

    def _schedule_save(self) -> None:
        """Queue preference saving on the Qt-aware asynchronous event loop."""
        asyncio.create_task(self.save())

    async def load(self) -> ThemePreference:
        """Load and show the persisted preference."""
        preference = await self._load_theme_preference.execute()
        self.preference_input.setText(preference.value)
        return preference

    async def save(self) -> ThemePreference | None:
        """Validate and save the user’s preference without exposing unrelated data."""
        try:
            preference = ThemePreference(self.preference_input.text().strip().lower())
            await self._save_theme_preference.execute(preference)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Unable to save theme")
            return None
        self.status_label.setText("Theme preference saved")
        return preference
