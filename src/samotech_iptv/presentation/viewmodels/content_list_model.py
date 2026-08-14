"""Lightweight Qt model for large movie and series catalogue projections."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QAbstractListModel, QModelIndex, QPersistentModelIndex, Qt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.content import ContentItemDTO

__all__ = ["ContentListModel"]

_ROOT_INDEX = QModelIndex()


class ContentListModel(QAbstractListModel):
    """Expose content summaries without allocating one widget per catalogue item."""

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ContentItemDTO] = []

    def rowCount(  # noqa: N802
        self,
        parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX,
    ) -> int:
        """Return the number of top-level content rows."""
        if parent.isValid():
            return 0
        return len(self._items)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> str | None:
        """Return safe display text for a valid content row."""
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        if role != int(Qt.ItemDataRole.DisplayRole):
            return None
        item = self._items[index.row()]
        metadata = []
        if item.year is not None:
            metadata.append(str(item.year))
        if item.rating is not None:
            metadata.append(f"★ {item.rating:g}")
        return " · ".join([item.title, *metadata])

    def item_at(self, row: int) -> ContentItemDTO:
        """Return the canonical presentation DTO associated with one model row."""
        return self._items[row]

    def replace_items(self, items: Sequence[ContentItemDTO]) -> None:
        """Replace all item references with one batched model reset."""
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
