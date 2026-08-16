"""Qt dialog for safe persisted-favorites browsing and removal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from samotech_iptv.presentation.task_owner import create_owned_task

if TYPE_CHECKING:
    from samotech_iptv.application.dtos import FavoriteDTO
    from samotech_iptv.application.use_cases.list_favorites import ListFavorites
    from samotech_iptv.application.use_cases.remove_favorite import RemoveFavorite

__all__ = ["FavoritesLibraryDialog"]

_LOAD_ERROR = "Unable to load favorites"
_REMOVE_ERROR = "Unable to remove favorite"


class FavoritesLibraryDialog(QDialog):
    """Render safe favorite summaries and remove one selected opaque record ID."""

    def __init__(
        self,
        list_favorites: ListFavorites,
        remove_favorite: RemoveFavorite,
    ) -> None:
        super().__init__()
        self._list_favorites = list_favorites
        self._remove_favorite = remove_favorite
        self._favorites: dict[str, FavoriteDTO] = {}
        self.favorite_summary_label = QLabel()
        self.favorite_id_input = QLineEdit()
        self.refresh_button = QPushButton("Refresh Favorites")
        self.refresh_button.clicked.connect(self._schedule_refresh)
        self.remove_button = QPushButton("Remove Selected Favorite")
        self.remove_button.clicked.connect(self._schedule_remove_selected)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow(self.favorite_summary_label)
        layout.addRow("Favorite ID", self.favorite_id_input)
        layout.addRow(self.refresh_button)
        layout.addRow(self.remove_button)
        layout.addRow(self.status_label)
        self.setWindowTitle("Favorites")

    async def refresh(self) -> None:
        """Refresh only presentation-safe favorite summaries."""
        response = await self._list_favorites.execute()
        if response.error is not None:
            self._favorites = {}
            self.favorite_summary_label.setText("No favorites available")
            self.status_label.setText(_LOAD_ERROR)
            return
        self._favorites = {favorite.id: favorite for favorite in response.favorites}
        self.favorite_summary_label.setText(
            "\n".join(
                f"{favorite.id} · {favorite.provider_id or 'legacy provider'} · "
                f"{favorite.item_type} · {favorite.item_id}"
                for favorite in response.favorites
            )
            or "No favorites saved"
        )
        self.status_label.setText("" if response.favorites else "No favorites saved")

    async def remove_selected(self) -> None:
        """Remove the selected favorite with generic feedback and a refreshed list."""
        favorite = self._favorites.get(self.favorite_id_input.text().strip())
        if favorite is None:
            self.status_label.setText("Select a saved favorite")
            return
        response = await self._remove_favorite.execute(favorite.id)
        if response.error is not None:
            self.status_label.setText(_REMOVE_ERROR)
            return
        if not response.removed:
            self.status_label.setText("Favorite no longer exists")
            await self.refresh()
            return
        self.favorite_id_input.clear()
        self.status_label.setText("Favorite removed")
        await self.refresh()

    def _schedule_refresh(self) -> None:
        """Queue refresh on the supported Qt-aware event loop."""
        create_owned_task(self, self.refresh())

    def _schedule_remove_selected(self) -> None:
        """Queue removal on the supported Qt-aware event loop."""
        create_owned_task(self, self.remove_selected())
