"""Qt dialog for saving the non-secret desktop theme preference."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
)

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

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
        self.preference_selector = QComboBox()
        self.preference_selector.addItem("System", ThemePreference.SYSTEM.value)
        self.preference_selector.addItem("Light", ThemePreference.LIGHT.value)
        self.preference_selector.addItem("Dark", ThemePreference.DARK.value)
        self.preference_selector.setAccessibleName("Theme preference")
        self.preference_selector.setToolTip("Choose system, light, or dark appearance")
        # Compatibility alias for callers that historically accessed the preference widget.
        self.preference_input = self.preference_selector
        self.save_button = QPushButton("Save Theme")
        self.save_button.setObjectName("primary")
        self.save_button.setAccessibleName("Save theme preference")
        self.save_button.clicked.connect(self._schedule_save)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Theme", self.preference_selector)
        layout.addRow(self.save_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Settings")
        apply_form_dialog_style(self)

    def _schedule_save(self) -> None:
        """Queue preference saving on the Qt-aware asynchronous event loop."""
        create_owned_task(self, self.save())

    async def load(self) -> ThemePreference:
        """Load and show the persisted preference."""
        preference = await self._load_theme_preference.execute()
        index = self.preference_selector.findData(preference.value)
        if index >= 0:
            self.preference_selector.setCurrentIndex(index)
        return preference

    async def save(self) -> ThemePreference | None:
        """Validate and save the user’s preference without exposing unrelated data."""
        try:
            preference = ThemePreference(str(self.preference_selector.currentData()))
            await self._save_theme_preference.execute(preference)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Unable to save theme")
            return None
        self.status_label.setText("Theme preference saved")
        return preference
