"""PySide6 provider summary dialog that never renders credentials or source URLs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.list_providers import ListProviders

__all__ = ["ProviderListDialog"]


class ProviderListDialog(QDialog):  # type: ignore[misc]
    """Render registered provider summaries without credential or source disclosure."""

    def __init__(self, list_providers: ListProviders) -> None:
        super().__init__()
        self._list_providers = list_providers
        self.provider_summary_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.provider_summary_label)
        self.setWindowTitle("Registered Providers")

    async def refresh(self) -> None:
        """Refresh the display with safe provider identifiers, types, and states only."""
        providers = await self._list_providers.execute()
        self.provider_summary_label.setText(
            "\n".join(
                f"{provider.id} · {provider.type} · "
                f"{'Active' if provider.is_active else 'Inactive'}"
                for provider in providers
            )
            or "No providers registered"
        )
