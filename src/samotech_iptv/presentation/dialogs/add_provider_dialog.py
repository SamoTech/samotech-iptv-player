"""Combined Smart Import and Manual Add entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from collections.abc import Callable

    from samotech_iptv.presentation.dialogs.smart_import_dialog import SmartImportDialog

__all__ = ["AddProviderDialog"]


class AddProviderDialog(QDialog):
    """Expose both provider-entry methods without replacing manual protocol dialogs."""

    def __init__(
        self,
        open_smart_import: Callable[[], SmartImportDialog],
        open_xtream: Callable[[], object],
        open_m3u: Callable[[], object],
        open_mag: Callable[[], object],
        parent: QWidget | None = None,
    ) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
        self._open_smart_import = open_smart_import
        self._open_xtream = open_xtream
        self._open_m3u = open_m3u
        self._open_mag = open_mag
        self._active_smart_import: SmartImportDialog | None = None
        self._active_manual_dialog: object | None = None

        tabs = QTabWidget()
        smart_page = QWidget()
        smart_layout = QVBoxLayout(smart_page)
        smart_layout.addWidget(
            QLabel("Paste IPTV information and SamoTech will detect the format locally.")
        )
        smart_button = QPushButton("Paste / Import from Clipboard")
        smart_button.setObjectName("primary")
        smart_button.setAccessibleName("Paste or import provider information")
        smart_button.setToolTip("Open smart import for locally detected provider details")
        smart_button.clicked.connect(self._show_smart_import)
        smart_layout.addWidget(smart_button)
        smart_layout.addWidget(QLabel("Paste → Detect → Review → Test → Add"))

        manual_page = QWidget()
        manual_layout = QVBoxLayout(manual_page)
        manual_layout.addWidget(
            QLabel("Enter provider details manually with full advanced control.")
        )
        xtream_button = QPushButton("Manual Xtream Add")
        xtream_button.setAccessibleName("Add Xtream provider manually")
        xtream_button.clicked.connect(self._show_xtream)
        m3u_button = QPushButton("Manual M3U Add")
        m3u_button.setAccessibleName("Add M3U provider manually")
        m3u_button.clicked.connect(self._show_m3u)
        mag_button = QPushButton("Manual MAG / Stalker Add")
        mag_button.setAccessibleName("Add MAG or Stalker provider manually")
        mag_button.clicked.connect(self._show_mag)
        manual_layout.addWidget(xtream_button)
        manual_layout.addWidget(m3u_button)
        manual_layout.addWidget(mag_button)
        manual_layout.addWidget(
            QLabel("Manual Add → Choose Provider Type → Fill Required Fields → Test → Add")
        )

        tabs.addTab(smart_page, "Smart Import")
        tabs.addTab(manual_page, "Manual Add")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("ADD IPTV PROVIDER"))
        layout.addWidget(tabs)
        self.setWindowTitle("Add IPTV Provider")
        apply_form_dialog_style(self)

    def _show_smart_import(self) -> None:
        self._active_smart_import = self._open_smart_import()

    def _show_xtream(self) -> None:
        self._active_manual_dialog = self._open_xtream()

    def _show_m3u(self) -> None:
        self._active_manual_dialog = self._open_m3u()

    def _show_mag(self) -> None:
        self._active_manual_dialog = self._open_mag()
