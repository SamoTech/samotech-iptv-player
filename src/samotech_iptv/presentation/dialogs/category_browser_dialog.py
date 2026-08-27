"""Browse-only registered-provider live-category dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
)

from samotech_iptv.application.dtos.categories import CategoryDTO, LoadCategoriesRequest
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.categories import LoadCategoriesResponse
    from samotech_iptv.application.use_cases.load_categories import LoadCategories

__all__ = ["CategoryBrowserDialog"]


class CategoryBrowserDialog(QDialog):
    """Browse canonical live categories without selecting, resolving, or playing content."""

    def __init__(self, load_categories: LoadCategories) -> None:
        super().__init__()
        self._load_categories = load_categories
        self._categories: list[CategoryDTO] = []
        self.provider_id_input = QLineEdit()
        self.category_list = QListWidget()
        self.load_categories_button = QPushButton("Load Live Categories")
        self.load_categories_button.clicked.connect(self._schedule_category_load)
        self.status_label = QLabel()
        layout = QFormLayout(self)
        layout.addRow("Provider ID", self.provider_id_input)
        layout.addRow(self.load_categories_button)
        layout.addRow("Live categories", self.category_list)
        layout.addRow(self.status_label)
        self.setWindowTitle("Browse Live Categories")
        apply_form_dialog_style(self)

    def _schedule_category_load(self) -> None:
        """Queue asynchronous category loading on the supported Qt-aware event loop."""
        create_owned_task(self, self.load_categories())

    async def load_categories(self) -> LoadCategoriesResponse:
        """Load and render safe canonical live-category summaries for one provider."""
        response = await self._load_categories.execute(
            LoadCategoriesRequest(provider_id=self.provider_id_input.text())
        )
        if response.error is not None:
            self._render_categories([])
            self.status_label.setText("Unable to load live categories")
            return response
        self._render_categories(response.categories)
        self.status_label.setText(
            f"{len(response.categories)} live categories loaded"
            if response.categories
            else "No live categories found"
        )
        return response

    def _render_categories(self, categories: Sequence[CategoryDTO]) -> None:
        """Render names only while retaining canonical category DTOs privately."""
        self.category_list.clear()
        self._categories = list(categories)
        for category in self._categories:
            self.category_list.addItem(category.name)
