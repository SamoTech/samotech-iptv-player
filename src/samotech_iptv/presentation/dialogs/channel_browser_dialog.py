"""Qt dialog for safely browsing and selecting channels from registered providers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
)

from samotech_iptv.application.dtos import ChannelDTO, LoadChannelsRequest, LoadChannelsResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels

__all__ = ["ChannelBrowserDialog"]


class ChannelBrowserDialog(QDialog):  # type: ignore[misc]
    """Browse safe channel rows and request selected-channel playback through a callback."""

    def __init__(
        self,
        browse_channels: BrowseChannels,
        play_selected_channel: Callable[[str, str], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__()
        self._browse_channels = browse_channels
        self._play_selected_channel = play_selected_channel
        self._channels: list[ChannelDTO] = []
        self.provider_id_input = QLineEdit()
        self.channel_list = QListWidget()
        self.load_channels_button = QPushButton("Load Channels")
        self.load_channels_button.clicked.connect(self._schedule_channel_load)
        self.channel_list.itemDoubleClicked.connect(self._schedule_selected_channel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow(self.load_channels_button)
        layout.addRow("Channels", self.channel_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Browse Channels")

    def _schedule_channel_load(self) -> None:
        """Queue asynchronous catalogue loading on the supported Qt-aware event loop."""
        asyncio.create_task(self.load_channels())

    def _schedule_selected_channel(self, _: object) -> None:
        """Queue playback for the current safe channel row when playback is configured."""
        row = self.channel_list.currentRow()
        if self._play_selected_channel is None or row < 0 or row >= len(self._channels):
            return
        asyncio.create_task(self._play_channel(row))

    async def _play_channel(self, row: int) -> None:
        """Delegate the selected channel identifiers without exposing stream URLs."""
        channel = self._channels[row]
        try:
            await self._play_selected_channel(channel.provider_id, channel.id)  # type: ignore[misc]
        except Exception:  # noqa: BLE001
            self.status_label.setText("Unable to play selected channel")
            return
        self.status_label.setText(f"Playing {channel.name}")

    async def load_channels(self) -> LoadChannelsResponse:
        """Load and render safe channel summary rows for the requested provider."""
        response = await self._browse_channels.execute(
            LoadChannelsRequest(provider_id=self.provider_id_input.text())
        )
        self.channel_list.clear()
        self._channels = []
        if response.error is not None:
            self.status_label.setText("Unable to load channels")
            return response
        self._channels = list(response.channels)
        for channel in self._channels:
            self.channel_list.addItem(f"{channel.name} · {channel.stream_id}")
        self.status_label.setText(
            f"{response.total} channels loaded" if response.total else "No channels found"
        )
        return response
