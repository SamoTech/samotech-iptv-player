"""Tests for the non-secret PySide6 desktop theme settings dialog."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference


class FakeDialog:
    """Minimal QDialog double retaining the configured title."""

    def __init__(self) -> None:
        self.title: str | None = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def show(self) -> None:
        return None


class FakeFormLayout:
    """Minimal QFormLayout double that records dialog rows."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double retaining visible feedback."""

    def __init__(self, value: str = "") -> None:
        self.value = value

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeComboBox:
    """Minimal QComboBox double retaining finite theme choices."""

    def __init__(self) -> None:
        self.items: list[tuple[str, object]] = []
        self.index = 0

    def addItem(self, label: str, value: object) -> None:  # noqa: N802
        self.items.append((label, value))

    def findData(self, value: object) -> int:  # noqa: N802
        return next((index for index, item in enumerate(self.items) if item[1] == value), -1)

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        self.index = index

    def currentData(self) -> object:  # noqa: N802
        return self.items[self.index][1]

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None

    def setToolTip(self, _: str) -> None:  # noqa: N802
        return None


class FakeLineEdit:
    """Compatibility double for sibling dialog imports from the package namespace."""

    class EchoMode:
        Password = object()

    def __init__(self) -> None:
        self.value = ""

    def setEchoMode(self, _: object) -> None:  # noqa: N802
        return None


class FakeSignal:
    """Minimal Qt signal double that records connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeCheckBox:
    """Minimal QCheckBox double for sibling dialog imports."""

    def __init__(self, _: str) -> None:
        self.toggled = FakeSignal()

    def setAccessibleName(self, _: str) -> None:  # noqa: N802
        return None

    def setEnabled(self, _: bool) -> None:  # noqa: N802
        return None


class FakePushButton:
    """Minimal QPushButton double exposing the clicked signal."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.clicked = FakeSignal()


class FakeLoadThemePreference:
    """Load-use-case double with a deterministic persisted preference."""

    def __init__(self, preference: ThemePreference) -> None:
        self.preference = preference
        self.calls = 0

    async def execute(self) -> ThemePreference:
        self.calls += 1
        return self.preference


class FakeSaveThemePreference:
    """Save-use-case double with optional controlled failure behavior."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.preferences: list[ThemePreference] = []

    async def execute(self, preference: ThemePreference) -> None:
        if self.should_fail:
            raise RuntimeError("detailed persistence failure")
        self.preferences.append(preference)


def _install_fake_pyside6() -> None:
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = FakeCheckBox
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QComboBox = FakeComboBox
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QPushButton = FakePushButton
    sys.modules.setdefault("PySide6", ModuleType("PySide6"))
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.dialogs.theme_settings_dialog import (  # noqa: E402
    ThemeSettingsDialog,
)


def _dialog(
    preference: ThemePreference = ThemePreference.SYSTEM,
    should_fail: bool = False,
) -> tuple[ThemeSettingsDialog, FakeLoadThemePreference, FakeSaveThemePreference]:
    load_theme_preference = FakeLoadThemePreference(preference)
    save_theme_preference = FakeSaveThemePreference(should_fail)
    dialog = ThemeSettingsDialog(load_theme_preference, save_theme_preference)  # type: ignore[arg-type]
    return dialog, load_theme_preference, save_theme_preference


@pytest.mark.asyncio
async def test_theme_settings_dialog_loads_the_persisted_preference() -> None:
    dialog, load_theme_preference, _ = _dialog(ThemePreference.DARK)

    preference = await dialog.load()

    assert preference is ThemePreference.DARK
    assert load_theme_preference.calls == 1
    assert dialog.preference_selector.currentData() == ThemePreference.DARK.value


@pytest.mark.asyncio
async def test_theme_settings_dialog_validates_and_saves_a_supported_preference() -> None:
    dialog, _, save_theme_preference = _dialog()
    dialog.preference_selector.setCurrentIndex(
        dialog.preference_selector.findData(ThemePreference.LIGHT.value)
    )

    preference = await dialog.save()

    assert preference is ThemePreference.LIGHT
    assert save_theme_preference.preferences == [ThemePreference.LIGHT]
    assert dialog.status_label.value == "Theme preference saved"


@pytest.mark.asyncio
async def test_theme_settings_dialog_hides_save_failure_details() -> None:
    dialog, _, save_theme_preference = _dialog(should_fail=True)
    dialog.preference_selector.setCurrentIndex(
        dialog.preference_selector.findData(ThemePreference.DARK.value)
    )

    preference = await dialog.save()

    assert preference is None
    assert save_theme_preference.preferences == []
    assert dialog.status_label.value == "Unable to save theme"
    assert "persistence" not in dialog.status_label.value
