"""PySide6 registered-provider list with credential-safe edit and removal actions."""

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

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider import ProviderMetadata
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.provider_lifecycle import (
        RemoveProvider,
        UpdateProvider,
    )
    from samotech_iptv.presentation.dialogs.provider_edit_dialog import ProviderEditDialog

__all__ = ["ProviderListDialog"]


class ProviderListDialog(QDialog):
    """Render safe provider summaries and offer credential-safe lifecycle actions."""

    def __init__(
        self,
        list_providers: ListProviders,
        update_provider: UpdateProvider,
        remove_provider: RemoveProvider,
    ) -> None:
        super().__init__()
        self._list_providers = list_providers
        self._update_provider = update_provider
        self._remove_provider = remove_provider
        self._providers: dict[str, ProviderMetadata] = {}
        self._active_provider_edit_dialog: ProviderEditDialog | None = None
        self.provider_summary_label = QLabel()
        self.provider_id_input = QLineEdit()
        self.edit_button = QPushButton("Edit Selected Provider")
        self.edit_button.clicked.connect(self.open_edit_dialog)
        self.remove_button = QPushButton("Remove Selected Provider")
        self.remove_button.clicked.connect(self._schedule_remove_selected)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.provider_summary_label)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow(self.edit_button)
        layout.addRow(self.remove_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Registered Providers")

    async def refresh(self) -> None:
        """Refresh only safe provider identifiers, types, and active states."""
        providers = await self._list_providers.execute()
        self._providers = {provider.id: provider for provider in providers}
        self.provider_summary_label.setText(
            "\n".join(
                f"{provider.id} · {provider.type} · "
                f"{'Active' if provider.is_active else 'Inactive'}"
                for provider in providers
            )
            or "No providers registered"
        )

    def open_edit_dialog(self) -> ProviderEditDialog | None:
        """Open a type-aware editor for a cached safe provider summary."""
        provider = self._selected_provider()
        if provider is None:
            self.status_label.setText("Select a registered provider")
            return None
        from samotech_iptv.presentation.dialogs.provider_edit_dialog import ProviderEditDialog

        dialog = ProviderEditDialog(provider, self._update_provider)
        dialog.show()
        self._active_provider_edit_dialog = dialog
        return dialog

    def _schedule_remove_selected(self) -> None:
        """Queue provider deletion on the supported Qt-aware event loop."""
        asyncio.create_task(self.remove_selected())

    async def remove_selected(self) -> None:
        """Remove a selected provider with generic safe status feedback."""
        provider = self._selected_provider()
        if provider is None:
            self.status_label.setText("Select a registered provider")
            return
        response = await self._remove_provider.execute(provider.id)
        if response.provider_id is None:
            self.status_label.setText(response.error or "Unable to remove provider")
            return
        self.provider_id_input.clear()
        self.status_label.setText("Provider removed")
        await self.refresh()

    def _selected_provider(self) -> ProviderMetadata | None:
        """Find one provider using its safe identifier without exposing secrets."""
        return self._providers.get(self.provider_id_input.text().strip())
