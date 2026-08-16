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
    from samotech_iptv.application.dtos.favorites import FavoriteDTO
    from samotech_iptv.application.use_cases.list_favorites import ListFavorites
    from samotech_iptv.application.use_cases.remove_favorite import RemoveFavorite

__all__ = ["FavoriteLibraryDialog"]


class FavoriteLibraryDialog(QDialog):
    """Render persisted favorites and support single-record removal."""

    def __init__(self, list_favorites: ListFavorites, remove_favorite: RemoveFavorite) -> None:
        super().__init__()
        self._list_favorites = list_favorites
        self._remove_favorite = remove_favorite
        self._favorites: dict[str, FavoriteDTO] = {}
        self.favorite_summary_label = QLabel()
        self.favorite_id_input = QLineEdit()
        self.refresh_button = QPushButton("Refresh")
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

    def _schedule_refresh(self) -> None:
        create_owned_task(self, self.refresh())

    async def refresh(self) -> None:
        """Reload favorites and render a safe summary or generic error."""
        try:
            response = await self._list_favorites.execute()
        except Exception:  # noqa: BLE001
            self._show_error("Unable to load favorites")
            return
        if response.error:
            self._show_error(response.error)
            return
        self._favorites = {favorite.id: favorite for favorite in response.favorites}
        self.favorite_summary_label.setText(
            "\n".join(
                f"{favorite.id} · {favorite.item_type} · {favorite.item_id}"
                for favorite in response.favorites
            )
            or "No favorites saved"
        )
        self.status_label.setText("")

    def _schedule_remove_selected(self) -> None:
        create_owned_task(self, self.remove_selected())

    async def remove_selected(self) -> None:
        """Remove exactly one selected favorite and refresh the list."""
        favorite_id = self.favorite_id_input.text().strip()
        if favorite_id not in self._favorites:
            self.status_label.setText("Select a favorite")
            return
        try:
            response = await self._remove_favorite.execute(favorite_id)
        except Exception:  # noqa: BLE001
            self._show_error("Unable to remove favorite")
            return
        if response.error or not response.removed:
            self._show_error(response.error or "Unable to remove favorite")
            return
        self.favorite_id_input.clear()
        self.status_label.setText("Favorite removed")
        await self.refresh()

    def _show_error(self, message: str) -> None:
        self.status_label.setText(message or "Unable to load favorites")
