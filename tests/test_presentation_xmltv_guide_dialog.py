from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.application.dtos import (
    ConfigureXMLTVBindingResponse,
    EPGEntryDTO,
    RefreshXMLTVGuideResponse,
)


class FakeSignal:
    """Minimal Qt signal double recording connected callbacks."""

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

    def __init__(self) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeVBoxLayout:
    """Minimal QVBoxLayout double."""

    def __init__(self, _: object) -> None:
        self.items: list[object] = []

    def addLayout(self, layout: object) -> None:  # noqa: N802
        self.items.append(layout)

    def addWidget(self, widget: object) -> None:  # noqa: N802
        self.items.append(widget)


class FakeLabel:
    """Minimal QLabel double retaining safe status copy."""

    def __init__(self, value: str = "") -> None:
        self.value = value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double compatible with shared presentation imports."""

    class EchoMode:
        """Minimal echo-mode namespace."""

        Password = object()

    def __init__(self) -> None:
        self.value = ""
        self.placeholder = ""
        self.echo_mode: object | None = None

    def clear(self) -> None:
        self.value = ""

    def setEchoMode(self, echo_mode: object) -> None:  # noqa: N802
        self.echo_mode = echo_mode

    def setPlaceholderText(self, value: str) -> None:  # noqa: N802
        self.placeholder = value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value

    def text(self) -> str:
        return self.value


class FakeListWidget:
    """Minimal QListWidget double retaining safe rendered rows."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def addItem(self, value: str) -> None:  # noqa: N802
        self.items.append(value)

    def clear(self) -> None:
        self.items.clear()


class FakeCheckBox:
    """Minimal QCheckBox double for sibling dialog imports."""

    def __init__(self, _: str) -> None:
        self.toggled = FakeSignal()

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None

    def setEnabled(self, _: bool) -> None:  # noqa: N802
        return None


class FakeButton:
    """Minimal QPushButton double."""

    def __init__(self, _: str) -> None:
        self.clicked = FakeSignal()

    def setObjectName(self, _: str) -> None:  # noqa: N802
        return None

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = FakeCheckBox
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QVBoxLayout = FakeVBoxLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QListWidget = FakeListWidget
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.xmltv_guide_dialog import XMLTVGuideDialog  # noqa: E402


class FakeConfigureBinding:
    """Configuration-use-case double retaining the last safe request."""

    def __init__(self, response: ConfigureXMLTVBindingResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    async def execute(self, request: object) -> ConfigureXMLTVBindingResponse:
        self.requests.append(request)
        return self.response


class FakeRefreshGuide:
    """Refresh-use-case double retaining selected provider identifiers."""

    def __init__(self, response: RefreshXMLTVGuideResponse) -> None:
        self.response = response
        self.provider_ids: list[str] = []

    async def execute(self, request: object) -> RefreshXMLTVGuideResponse:
        self.provider_ids.append(request.provider_id)  # type: ignore[attr-defined]
        return self.response


def _dialog(
    configure_response: ConfigureXMLTVBindingResponse | None = None,
    refresh_response: RefreshXMLTVGuideResponse | None = None,
) -> tuple[XMLTVGuideDialog, FakeConfigureBinding, FakeRefreshGuide]:
    configure = FakeConfigureBinding(
        configure_response or ConfigureXMLTVBindingResponse(success=True)
    )
    refresh = FakeRefreshGuide(refresh_response or RefreshXMLTVGuideResponse())
    return XMLTVGuideDialog(configure, refresh), configure, refresh  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_configure_parses_explicit_mappings_and_never_echoes_source() -> None:
    dialog, configure, _ = _dialog()
    dialog.provider_id_input.setText("demo")
    dialog.source_input.setText("/guides/local.xml")
    dialog.mapping_input.setText("source.news=demo:news, source.sport=demo:sport")

    await dialog.configure()

    request = configure.requests[0]
    assert request.provider_id == "demo"  # type: ignore[attr-defined]
    assert [(item.source_channel_id, item.channel_id) for item in request.mappings] == [  # type: ignore[attr-defined]
        ("source.news", "demo:news"),
        ("source.sport", "demo:sport"),
    ]
    assert dialog.status_label.value == "Local XMLTV guide configuration saved"
    assert "/guides/local.xml" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_configure_reports_generic_error_for_invalid_mapping_input() -> None:
    dialog, configure, _ = _dialog()
    dialog.provider_id_input.setText("demo")
    dialog.source_input.setText("/guides/local.xml")
    dialog.mapping_input.setText("invalid-mapping")

    await dialog.configure()

    assert configure.requests == []
    assert dialog.status_label.value == "Unable to save XMLTV guide configuration"
    assert "/guides/local.xml" not in dialog.status_label.value


@pytest.mark.asyncio
async def test_refresh_renders_only_schedule_rows_and_hides_description() -> None:
    response = RefreshXMLTVGuideResponse(
        entries=(
            EPGEntryDTO(
                id="entry-1",
                channel_id="demo:news",
                title="Morning News",
                start="2026-08-13T01:00:00+00:00",
                end="2026-08-13T01:30:00+00:00",
                description="Private guide description",
            ),
        )
    )
    dialog, _, refresh = _dialog(refresh_response=response)
    dialog.provider_id_input.setText("demo")

    await dialog.refresh()

    assert refresh.provider_ids == ["demo"]
    assert dialog.entries_list.items == [
        "2026-08-13T01:00:00+00:00 — 2026-08-13T01:30:00+00:00 — Morning News"
    ]
    assert "Private" not in dialog.entries_list.items[0]
    assert dialog.status_label.value == "Loaded 1 entries"


@pytest.mark.asyncio
async def test_refresh_reports_generic_failure_without_source_detail() -> None:
    dialog, _, _ = _dialog(refresh_response=RefreshXMLTVGuideResponse(error="source unavailable"))
    dialog.provider_id_input.setText("demo")

    await dialog.refresh()

    assert dialog.entries_list.items == []
    assert dialog.status_label.value == "Unable to refresh XMLTV guide"
    assert "source unavailable" not in dialog.status_label.value
