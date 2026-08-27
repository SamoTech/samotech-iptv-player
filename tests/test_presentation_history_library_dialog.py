from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos import (
    ClearHistoryResponse,
    HistoryItemDTO,
    LoadHistoryResponse,
)


class FakeSignal:
    """Minimal signal double recording connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeMessageBox:
    """Deterministic QMessageBox double with a safe configurable response."""

    class StandardButton:
        Yes = 1
        No = 2

    response = StandardButton.Yes

    @classmethod
    def question(cls, *_args: object, **_kwargs: object) -> int:
        return cls.response


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


class FakeButton:
    """Minimal QPushButton double with accessible metadata support."""

    def __init__(self, _: str) -> None:
        self.clicked = FakeSignal()
        self.object_name = ""
        self.accessible_name = ""
        self.tooltip = ""

    def setObjectName(self, value: str) -> None:  # noqa: N802
        self.object_name = value

    def setAccessibleName(self, value: str) -> None:  # noqa: N802
        self.accessible_name = value

    def setToolTip(self, value: str) -> None:  # noqa: N802
        self.tooltip = value


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QMessageBox = FakeMessageBox
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.history_library_dialog import (  # noqa: E402
    HistoryLibraryDialog,
)


class FakeLoadHistory:
    """History-list use-case double returning deterministic responses."""

    def __init__(self, responses: list[LoadHistoryResponse]) -> None:
        self._responses = responses
        self.requests: list[object] = []

    async def execute(self, request: object) -> LoadHistoryResponse:
        self.requests.append(request)
        return self._responses.pop(0)


class FakeClearHistory:
    """History-clear use-case double returning a configured generic outcome."""

    def __init__(self, response: ClearHistoryResponse) -> None:
        self.response = response
        self.calls = 0

    async def execute(self) -> ClearHistoryResponse:
        self.calls += 1
        return self.response


def _dialog(
    load_responses: list[LoadHistoryResponse],
    clear_response: ClearHistoryResponse | None = None,
) -> tuple[HistoryLibraryDialog, FakeLoadHistory, FakeClearHistory]:
    load_history = FakeLoadHistory(load_responses)
    clear_history = FakeClearHistory(clear_response or ClearHistoryResponse(cleared=0))
    return HistoryLibraryDialog(load_history, clear_history), load_history, clear_history  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_history_refresh_renders_safe_user_progress_without_internal_identifiers() -> None:
    dialog, load_history, _ = _dialog(
        [
            LoadHistoryResponse(
                items=(
                    HistoryItemDTO(
                        id="history-1",
                        item_id="channel-1",
                        item_type="channel",
                        watched_at="2026-08-13T01:00:00+00:00",
                        duration_seconds=120,
                        position_seconds=30,
                    ),
                )
            )
        ]
    )

    await dialog.refresh()

    assert len(load_history.requests) == 1
    assert dialog.history_summary_label.value == (
        "Channel · Continue at 0:30 of 2:00 · Last watched 2026-08-13 01:00"
    )
    assert "history-1" not in dialog.history_summary_label.value
    assert "channel-1" not in dialog.history_summary_label.value
    assert dialog.status_label.value == ""


@pytest.mark.asyncio
async def test_history_refresh_displays_empty_state() -> None:
    dialog, _, _ = _dialog([LoadHistoryResponse()])

    await dialog.refresh()

    assert dialog.history_summary_label.value == "No history recorded"
    assert dialog.status_label.value == "No history recorded"


@pytest.mark.asyncio
async def test_history_refresh_hides_failure_detail() -> None:
    dialog, _, _ = _dialog([LoadHistoryResponse(error="private database detail")])

    await dialog.refresh()

    assert dialog.history_summary_label.value == "No history available"
    assert dialog.status_label.value == "Unable to load history"
    assert "private" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_history_clear_uses_existing_clear_all_boundary_and_refreshes() -> None:
    dialog, load_history, clear_history = _dialog(
        [LoadHistoryResponse()],
        ClearHistoryResponse(cleared=3),
    )

    await dialog.clear()

    assert clear_history.calls == 1
    assert len(load_history.requests) == 1
    assert dialog.status_label.value == "No history recorded"


@pytest.mark.asyncio
async def test_history_clear_hides_failure_detail() -> None:
    dialog, load_history, clear_history = _dialog(
        [],
        ClearHistoryResponse(cleared=0, error="private database detail"),
    )

    await dialog.clear()

    assert clear_history.calls == 1
    assert load_history.requests == []
    assert dialog.status_label.value == "Unable to clear history"
    assert "private" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_history_clear_requires_explicit_confirmation() -> None:
    dialog, load_history, clear_history = _dialog(
        [],
        ClearHistoryResponse(cleared=3),
    )
    FakeMessageBox.response = FakeMessageBox.StandardButton.No

    await dialog.clear()

    FakeMessageBox.response = FakeMessageBox.StandardButton.Yes
    assert clear_history.calls == 0
    assert load_history.requests == []
    assert dialog.status_label.value == "History clear canceled"
