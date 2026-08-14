"""Lightweight Qt model for large registered-provider channel catalogues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.channels import ChannelDTO

__all__ = ["ChannelListModel"]


class ChannelListModel(QAbstractListModel):  # type: ignore[misc]
    """Expose safe channel summaries without allocating one widget per channel."""

    def __init__(self) -> None:
        super().__init__()
        self._channels: list[ChannelDTO] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        """Return the number of top-level channel rows."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._channels)

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)) -> str | None:
        """Return safe display text for a valid channel row."""
        if not index.isValid() or not 0 <= index.row() < len(self._channels):
            return None
        if role != int(Qt.ItemDataRole.DisplayRole):
            return None
        channel = self._channels[index.row()]
        return f"{channel.name} · {channel.stream_id}"

    def channel_at(self, row: int) -> ChannelDTO:
        """Return the canonical DTO associated with one model row."""
        return self._channels[row]

    def replace_channels(self, channels: Sequence[ChannelDTO]) -> None:
        """Replace all channel references with one batched model reset."""
        self.beginResetModel()
        self._channels = list(channels)
        self.endResetModel()
