from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos import (
    FavoriteDTO,
    ListFavoritesResponse,
    RemoveFavoriteResponse,
)


class FakeSignal:
    """Minimal signal double recording connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeDialog:
    """Minimal QDialog double."""

    def __init__(self) -> None:
        self.title = ""

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def show(self) -> None:
        return None


class FakeFormLayout:
    """Minimal QFormLayout double."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double retaining status and summary copy."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeListWidget:
    """Minimal selectable list double for safe favorite summaries."""

    def __init__(self) -> None:
        self.items: list[str] = []
        self.selected_row = -1

    def addItem(self, item: str) -> None:  # noqa: N802
        self.items.append(item)

    def clear(self) -> None:
        self.items.clear()
        self.selected_row = -1

    def currentRow(self) -> int:  # noqa: N802
        return self.selected_row

    def setCurrentRow(self, row: int) -> None:  # noqa: N802
        self.selected_row = row


class FakeLineEdit:
    """Minimal import-compatible line-edit stub for sibling dialog modules."""

    class EchoMode:
        Password = object()

    def __init__(self) -> None:
        self.value = ""

    def text(self) -> str:
        return self.value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, _: object) -> None:  # noqa: N802
        return None


class FakeButton:
    """Minimal QPushButton double."""

    def __init__(self, _: str) -> None:
        self.clicked = FakeSignal()


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QListWidget = FakeListWidget
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.favorites_library_dialog import (  # noqa: E402
    FavoritesLibraryDialog,
)


class FakeListFavorites:
    """Favorites-list use-case double returning deterministic responses."""

    def __init__(self, responses: list[ListFavoritesResponse]) -> None:
        self._responses = responses
        self.calls = 0

    async def execute(self) -> ListFavoritesResponse:
        self.calls += 1
        return self._responses.pop(0)


class FakeRemoveFavorite:
    """Favorite-removal double retaining opaque canonical record IDs."""

    def __init__(self, response: RemoveFavoriteResponse) -> None:
        self.response = response
        self.ids: list[str] = []

    async def execute(self, favorite_id: str) -> RemoveFavoriteResponse:
        self.ids.append(favorite_id)
        return self.response


def _dialog(
    list_responses: list[ListFavoritesResponse],
    remove_response: RemoveFavoriteResponse | None = None,
) -> tuple[FavoritesLibraryDialog, FakeListFavorites, FakeRemoveFavorite]:
    list_favorites = FakeListFavorites(list_responses)
    remove_favorite = FakeRemoveFavorite(remove_response or RemoveFavoriteResponse(removed=True))
    return FavoritesLibraryDialog(list_favorites, remove_favorite), list_favorites, remove_favorite  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_favorites_refresh_renders_safe_user_summary_without_internal_identifiers() -> None:
    dialog, list_favorites, _ = _dialog(
        [
            ListFavoritesResponse(
                favorites=(
                    FavoriteDTO(
                        id="favorite-1",
                        item_id="channel-1",
                        item_type="channel",
                        added_at="2026-08-13T01:00:00+00:00",
                    ),
                )
            )
        ]
    )

    await dialog.refresh()

    assert list_favorites.calls == 1
    assert dialog.favorite_summary_label.value == "1 saved favorite"
    assert dialog.favorite_list.items == ["Favorite 1 · Channel"]
    assert "favorite-1" not in dialog.favorite_list.items[0]
    assert "channel-1" not in dialog.favorite_list.items[0]
    assert dialog.status_label.value == ""


@pytest.mark.asyncio
async def test_favorites_refresh_displays_empty_state() -> None:
    dialog, _, _ = _dialog([ListFavoritesResponse()])

    await dialog.refresh()

    assert dialog.favorite_summary_label.value == "No favorites saved"
    assert dialog.status_label.value == (
        "No favorites saved. Add a channel, movie, or series to see it here."
    )


@pytest.mark.asyncio
async def test_favorites_refresh_hides_failure_details() -> None:
    dialog, _, _ = _dialog([ListFavoritesResponse(error="private storage detail")])

    await dialog.refresh()

    assert dialog.favorite_summary_label.value == "No favorites available"
    assert dialog.status_label.value == "Unable to load favorites"
    assert "private" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_selected_favorite_removal_uses_canonical_record_id_and_refreshes() -> None:
    favorite = FavoriteDTO(
        id="favorite-1",
        item_id="channel-1",
        item_type="channel",
        added_at="2026-08-13T01:00:00+00:00",
    )
    dialog, list_favorites, remove_favorite = _dialog(
        [ListFavoritesResponse(favorites=(favorite,)), ListFavoritesResponse()]
    )
    await dialog.refresh()
    dialog.favorite_list.setCurrentRow(0)

    await dialog.remove_selected()

    assert remove_favorite.ids == ["favorite-1"]
    assert list_favorites.calls == 2
    assert dialog.favorite_summary_label.value == "No favorites saved"
    assert "No favorites saved" in dialog.status_label.value


@pytest.mark.asyncio
async def test_favorite_removal_hides_failure_detail() -> None:
    favorite = FavoriteDTO(
        id="favorite-1",
        item_id="channel-1",
        item_type="channel",
        added_at="2026-08-13T01:00:00+00:00",
    )
    dialog, _, remove_favorite = _dialog(
        [ListFavoritesResponse(favorites=(favorite,))],
        RemoveFavoriteResponse(removed=False, error="private storage detail"),
    )
    await dialog.refresh()
    dialog.favorite_list.setCurrentRow(0)

    await dialog.remove_selected()

    assert remove_favorite.ids == ["favorite-1"]
    assert dialog.status_label.value == "Unable to remove favorite"
    assert "private" not in dialog.status_label.value
