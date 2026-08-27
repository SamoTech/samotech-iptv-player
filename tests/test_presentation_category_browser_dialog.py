"""Presentation tests for browse-only registered live-category discovery."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos.categories import (
    CategoryDTO,
    LoadCategoriesResponse,
)


class FakeSignal:
    """Minimal Qt signal double."""

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


class FakeFormLayout:
    """Minimal QFormLayout double."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double compatible with shared dialog imports."""

    class EchoMode:
        """Minimal echo-mode namespace."""

        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.echo_mode: object | None = None

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, echo_mode: object) -> None:  # noqa: N802
        self.echo_mode = echo_mode

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def text(self) -> str:
        return self.value


class FakeListWidget:
    """Minimal QListWidget double retaining rendered summary rows."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def addItem(self, item: str) -> None:  # noqa: N802
        self.items.append(item)

    def clear(self) -> None:
        self.items.clear()


class FakeButton:
    """Minimal QPushButton double."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QListWidget = FakeListWidget
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.category_browser_dialog import (  # noqa: E402
    CategoryBrowserDialog,
)


class FakeLoadCategories:
    """Use-case double returning deterministic safe catalogue responses."""

    def __init__(self, response: LoadCategoriesResponse) -> None:
        self.response = response
        self.provider_ids: list[str] = []

    async def execute(self, request: object) -> LoadCategoriesResponse:
        self.provider_ids.append(request.provider_id)
        return self.response


@pytest.mark.asyncio
async def test_category_browser_loads_safe_canonical_rows_for_selected_provider() -> None:
    """The dialog renders category names without provider configuration or playback paths."""
    load_categories = FakeLoadCategories(
        LoadCategoriesResponse(
            categories=[
                CategoryDTO(id="news", name="News", provider_id="xtream-demo"),
                CategoryDTO(id="sports", name="Sports", provider_id="xtream-demo"),
            ]
        )
    )
    dialog = CategoryBrowserDialog(load_categories)  # type: ignore[arg-type]
    dialog.provider_id_input.setText("xtream-demo")

    response = await dialog.load_categories()

    assert response.error is None
    assert load_categories.provider_ids == ["xtream-demo"]
    assert dialog.category_list.items == ["News", "Sports"]
    assert dialog.status_label.value == "2 live categories loaded"
    assert dialog.load_categories_button.clicked.callbacks == [dialog._schedule_category_load]
    assert "xtream-demo" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_category_browser_reports_empty_catalogue_without_error() -> None:
    """An empty live category result is rendered as a normal catalogue state."""
    dialog = CategoryBrowserDialog(
        FakeLoadCategories(LoadCategoriesResponse())  # type: ignore[arg-type]
    )

    await dialog.load_categories()

    assert dialog.category_list.items == []
    assert dialog.status_label.value == "No live categories found"


@pytest.mark.asyncio
async def test_category_browser_hides_provider_failure_details() -> None:
    """Failure status remains generic even if a lower layer supplies sensitive detail."""
    dialog = CategoryBrowserDialog(
        FakeLoadCategories(
            LoadCategoriesResponse(error="credential token rejected")
        )  # type: ignore[arg-type]
    )
    dialog.category_list.addItem("Old safe row")

    await dialog.load_categories()

    assert dialog.category_list.items == []
    assert dialog.status_label.value == "Unable to load live categories"
    assert "credential" not in dialog.status_label.value
    assert "token" not in dialog.status_label.value
