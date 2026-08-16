"""Qt dialog for safely browsing, searching, and selecting registered-provider channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
)

from samotech_iptv.application.dtos import ChannelDTO, LoadChannelsRequest, LoadChannelsResponse
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.viewmodels.channel_list_model import ChannelListModel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
    from samotech_iptv.application.use_cases.search_registered_channels import (
        SearchRegisteredChannels,
    )

__all__ = ["ChannelBrowserDialog"]


class ChannelBrowserDialog(QDialog):
    """Browse, search, and select safe channel rows through application callbacks."""

    def __init__(
        self,
        browse_channels: BrowseChannels,
        play_selected_channel: Callable[[str, str], Awaitable[None]] | None = None,
        search_channels: SearchRegisteredChannels | None = None,
        save_favorite: SaveFavorite | None = None,
    ) -> None:
        super().__init__()
        self._browse_channels = browse_channels
        self._play_selected_channel = play_selected_channel
        self._search_channels = search_channels
        self._save_favorite = save_favorite
        self._channels: list[ChannelDTO] = []
        self.provider_id_input = QLineEdit()
        self.search_query_input = QLineEdit()
        self.channel_list = QListView()
        self.channel_model = ChannelListModel()
        self.channel_list.setModel(self.channel_model)
        self.load_channels_button = QPushButton("Load Channels")
        self.search_channels_button = QPushButton("Search")
        self.add_favorite_button = QPushButton("Add Favorite")
        self.load_channels_button.clicked.connect(self._schedule_channel_load)
        self.search_channels_button.clicked.connect(self._schedule_channel_search)
        self.add_favorite_button.clicked.connect(self._schedule_add_favorite)
        self.channel_list.doubleClicked.connect(self._schedule_selected_channel)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow(self.load_channels_button)
        layout.addRow("Search channels", self.search_query_input)
        layout.addRow(self.search_channels_button)
        layout.addRow(self.add_favorite_button)
        layout.addRow("Channels", self.channel_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Browse Channels")

    def _schedule_channel_load(self) -> None:
        """Queue asynchronous catalogue loading on the supported Qt-aware event loop."""
        create_owned_task(self, self.load_channels())

    def _schedule_channel_search(self) -> None:
        """Queue provider-scoped channel search on the supported Qt-aware event loop."""
        if self._search_channels is not None:
            create_owned_task(self, self.search_channels())

    def _schedule_add_favorite(self) -> None:
        """Queue saving the current selected channel as a user favorite."""
        row = self.channel_list.currentIndex().row()
        if self._save_favorite is not None and 0 <= row < len(self._channels):
            channel = self.channel_model.channel_at(row)
            create_owned_task(self, self.add_favorite(channel))

    def _schedule_selected_channel(self, _: object) -> None:
        """Queue playback for the current safe channel row when playback is configured."""
        row = self.channel_list.currentIndex().row()
        if self._play_selected_channel is None or row < 0 or row >= len(self._channels):
            return
        channel = self.channel_model.channel_at(row)
        create_owned_task(self, self._play_channel(channel))

    async def add_favorite(self, channel: ChannelDTO | int) -> None:
        """Save only the selected channel identifier through the application boundary."""
        save_favorite = self._save_favorite
        if save_favorite is None:
            return
        target = self.channel_model.channel_at(channel) if isinstance(channel, int) else channel
        from samotech_iptv.application.dtos import SaveFavoriteRequest

        response = await save_favorite.execute(
            SaveFavoriteRequest(item_id=target.id, item_type="channel")
        )
        self.status_label.setText(
            "Channel added to favorites" if response.success else "Unable to add favorite"
        )

    async def _play_channel(self, channel: ChannelDTO | int) -> None:
        """Delegate the selected channel identifiers without exposing stream URLs."""
        target = self.channel_model.channel_at(channel) if isinstance(channel, int) else channel
        callback = self._play_selected_channel
        if callback is None:
            return
        try:
            await callback(target.provider_id, target.id)
        except Exception:  # noqa: BLE001
            self.status_label.setText("Unable to play selected channel")
            return
        self.status_label.setText(f"Playing {target.name}")

    async def load_channels(self) -> LoadChannelsResponse:
        """Load and render safe channel summary rows for the requested provider."""
        response = await self._browse_channels.execute(
            LoadChannelsRequest(provider_id=self.provider_id_input.text())
        )
        if response.error is not None:
            self._render_channels([])
            self.status_label.setText("Unable to load channels")
            return response
        self._render_channels(response.channels)
        self.status_label.setText(
            f"{response.total} channels loaded" if response.total else "No channels found"
        )
        return response

    async def search_channels(self) -> None:
        """Search the selected registered provider and render safe matching rows."""
        search_channels = self._search_channels
        if search_channels is None:
            return
        from samotech_iptv.application.dtos import SearchRegisteredChannelsRequest

        try:
            response = await search_channels.execute(
                SearchRegisteredChannelsRequest(
                    provider_id=self.provider_id_input.text(),
                    query=self.search_query_input.text(),
                )
            )
        except Exception:  # noqa: BLE001
            self._render_channels([])
            self.status_label.setText("Unable to search channels")
            return
        self._render_channels(response.channels)
        self.status_label.setText(
            f"{response.total} channels found" if response.total else "No matching channels"
        )

    def _render_channels(self, channels: Sequence[ChannelDTO]) -> None:
        """Render only channel names and stream IDs, retaining IDs in private dialog state."""
        self._channels = list(channels)
        self.channel_model.replace_channels(self._channels)
