"""Qt dialog for safely browsing channels from a registered provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
)

from samotech_iptv.application.dtos import LoadChannelsRequest, LoadChannelsResponse

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels

__all__ = ["ChannelBrowserDialog"]


class ChannelBrowserDialog(QDialog):  # type: ignore[misc]
    """Load a registered provider's channels without displaying secrets or stream URLs."""

    def __init__(self, browse_channels: BrowseChannels) -> None:
        super().__init__()
        self._browse_channels = browse_channels
        self.provider_id_input = QLineEdit()
        self.channel_list = QListWidget()
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow("Channels", self.channel_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Browse Channels")

    async def load_channels(self) -> LoadChannelsResponse:
        """Load and render safe channel summary rows for the requested provider."""
        response = await self._browse_channels.execute(
            LoadChannelsRequest(provider_id=self.provider_id_input.text())
        )
        self.channel_list.clear()
        if response.error is not None:
            self.status_label.setText("Unable to load channels")
            return response
        for channel in response.channels:
            self.channel_list.addItem(f"{channel.name} · {channel.stream_id}")
        self.status_label.setText(
            f"{response.total} channels loaded" if response.total else "No channels found"
        )
        return response
