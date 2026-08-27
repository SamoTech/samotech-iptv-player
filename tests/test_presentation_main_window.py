"""Tests for the initial PySide6 VLC playback main window."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

from samotech_iptv.domain.value_objects.theme_preference import ThemePreference


class FakeFrame:
    """Minimal QFrame double for the hosted native video surface."""

    def __init__(self) -> None:
        self.styles: list[str] = []

    def setAttribute(self, _: object) -> None:  # noqa: N802
        return None

    def setStyleSheet(self, style: str) -> None:  # noqa: N802
        self.styles.append(style)

    def winId(self) -> int:  # noqa: N802
        return 789

    def showEvent(self, _: object) -> None:  # noqa: N802
        return None


class FakeDialog:
    """Minimal QDialog double for imported provider-entry dialog construction."""

    def __init__(self) -> None:
        self.title: str | None = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def show(self) -> None:
        return None


class FakeFormLayout:
    """Minimal QFormLayout double for imported provider-entry dialog construction."""

    def __init__(self, _: object) -> None:
        self.rows: list[tuple[object, ...]] = []

    def addRow(self, *row: object) -> None:  # noqa: N802
        self.rows.append(row)


class FakeLabel:
    """Minimal QLabel double retaining dialog feedback copy."""

    def __init__(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:  # noqa: N802
        self.value = value


class FakeLineEdit:
    """Minimal QLineEdit double for imported provider-entry dialog construction."""

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


class FakeComboBox:
    """Minimal finite-choice selector double for the theme dialog fallback."""

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


class FakeButton:
    """Minimal QPushButton double retaining its signal contract."""

    def __init__(self, _: str) -> None:
        self.clicked = FakeSignal()


class FakeSignal:
    """Minimal Qt signal double that records connected callbacks."""

    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class FakeAction:
    """Minimal QAction double for menu-action composition verification."""

    def __init__(self, text: str, _: object) -> None:
        self.text = text
        self.triggered = FakeSignal()


class FakeMenu:
    """Minimal QMenu double that records its actions."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.actions: list[FakeAction] = []

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeMenuBar:
    """Minimal QMenuBar double that records its menus."""

    def __init__(self) -> None:
        self.menus: list[FakeMenu] = []
        self.actions: list[FakeAction] = []

    def addMenu(self, title: str) -> FakeMenu:  # noqa: N802
        menu = FakeMenu(title)
        self.menus.append(menu)
        return menu

    def addAction(self, action: FakeAction) -> None:  # noqa: N802
        self.actions.append(action)


class FakeStatusBar:
    """Minimal QStatusBar double retaining safe status feedback."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.messages.append(message)


class FakeMainWindow:
    """Minimal QMainWindow double for composition verification."""

    def __init__(self) -> None:
        self.central_widget: object | None = None
        self.title: str | None = None
        self.menu_bar = FakeMenuBar()
        self.status_bar = FakeStatusBar()

    def setCentralWidget(self, widget: object) -> None:  # noqa: N802
        self.central_widget = widget

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self.title = title

    def menuBar(self) -> FakeMenuBar:  # noqa: N802
        return self.menu_bar

    def statusBar(self) -> FakeStatusBar:  # noqa: N802
        return self.status_bar


class FakePlayer:
    """Player-port double that records native output attachment."""

    def __init__(self) -> None:
        self.native_window_ids: list[int] = []

    def attach_video_output(self, native_window_id: int) -> None:
        self.native_window_ids.append(native_window_id)


class FakeRegistration:
    """Registration-use-case double required by main-window composition."""

    async def execute(self, _: object) -> object:
        return object()


class FakePlayChannel:
    """Application-use-case double that records presentation requests."""

    def __init__(self) -> None:
        self.channel_ids: list[str] = []

    async def execute(self, channel_id: str) -> None:
        self.channel_ids.append(channel_id)


class FakeRecording:
    """Recording use-case double with configurable generic failure behavior."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = 0

    async def execute(self) -> None:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("local recording output failed")


class FakePlaybackControl:
    """Generic playback-control double with configurable safe failure behavior."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = 0

    async def execute(self) -> None:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("resolved stream URL rejected")


class FakeThemeLoad:
    """Theme-load double that returns a deterministic persisted preference."""

    def __init__(self, preference: ThemePreference = ThemePreference.SYSTEM) -> None:
        self.preference = preference
        self.calls = 0

    async def execute(self) -> ThemePreference:
        self.calls += 1
        return self.preference


class FakeThemeSave:
    """Theme-save double that records the selected desktop preference."""

    def __init__(self) -> None:
        self.preferences: list[ThemePreference] = []

    async def execute(self, preference: ThemePreference) -> None:
        self.preferences.append(preference)


def _install_fake_pyside6() -> None:
    qtcore = ModuleType("PySide6.QtCore")
    qtcore.Qt = SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_NativeWindow=object()))
    qtgui = ModuleType("PySide6.QtGui")
    qtgui.QAction = FakeAction
    qtgui.QShowEvent = object
    qtwidgets = ModuleType("PySide6.QtWidgets")
    qtwidgets.QCheckBox = type("FakeCheckBox", (), {})
    qtwidgets.QFrame = FakeFrame
    qtwidgets.QMainWindow = FakeMainWindow
    qtwidgets.QDialog = FakeDialog
    qtwidgets.QFormLayout = FakeFormLayout
    qtwidgets.QLabel = FakeLabel
    qtwidgets.QLineEdit = FakeLineEdit
    qtwidgets.QComboBox = FakeComboBox
    qtwidgets.QPushButton = FakeButton
    sys.modules["PySide6"] = ModuleType("PySide6")
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_fake_pyside6()

from samotech_iptv.presentation.views.main_window import MainWindow  # noqa: E402


@pytest.mark.asyncio
async def test_main_window_reports_safe_recording_status() -> None:
    start_recording = FakeRecording()
    stop_recording = FakeRecording()
    pause_playback = FakePlaybackControl()
    resume_playback = FakePlaybackControl()
    stop_playback = FakePlaybackControl()
    window = MainWindow(
        FakePlayer(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeThemeLoad(),
        FakeThemeSave(),
        start_recording,
        stop_recording,
        pause_playback,
        resume_playback,
        stop_playback,
    )  # type: ignore[arg-type]

    await window.pause_playback()
    await window.resume_playback()
    await window.stop_playback()
    await window.start_recording()
    await window.stop_recording()

    assert pause_playback.calls == 1
    assert resume_playback.calls == 1
    assert stop_playback.calls == 1
    assert start_recording.calls == 1
    assert stop_recording.calls == 1
    assert window.status_bar.messages == [
        "Playback paused",
        "Playback resumed",
        "Playback stopped",
        "Recording started",
        "Recording stopped",
    ]


@pytest.mark.asyncio
async def test_main_window_hides_recording_failure_details() -> None:
    window = MainWindow(
        FakePlayer(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeThemeLoad(),
        FakeThemeSave(),
        FakeRecording(should_fail=True),
        FakeRecording(should_fail=True),
        FakePlaybackControl(should_fail=True),
        FakePlaybackControl(should_fail=True),
        FakePlaybackControl(should_fail=True),
    )  # type: ignore[arg-type]

    await window.pause_playback()
    await window.resume_playback()
    await window.stop_playback()
    await window.start_recording()
    await window.stop_recording()

    assert window.status_bar.messages == [
        "Unable to pause playback",
        "Unable to resume playback",
        "Unable to stop playback",
        "Unable to start recording",
        "Unable to stop recording",
    ]
    assert all("output" not in message for message in window.status_bar.messages)
    assert all("URL" not in message for message in window.status_bar.messages)


def test_main_window_exposes_xtream_provider_menu_action() -> None:
    window = MainWindow(
        FakePlayer(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeThemeLoad(),
        FakeThemeSave(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlaybackControl(),
        FakePlaybackControl(),
        FakePlaybackControl(),
    )  # type: ignore[arg-type]

    assert window.menu_bar.menus[0].title == "Providers"
    assert window.menu_bar.menus[0].actions == [
        window.add_provider_action,
        window.add_xtream_provider_action,
        window.add_m3u_provider_action,
        window.add_mag_provider_action,
        window.browse_channels_action,
        window.browse_live_categories_action,
        window.show_epg_action,
        window.xmltv_guide_action,
        window.show_provider_list_action,
    ]
    assert window.add_xtream_provider_action.text == "Add Xtream Provider…"
    assert window.add_xtream_provider_action.triggered.callbacks == [
        window.open_xtream_provider_dialog
    ]
    assert window.add_m3u_provider_action.text == "Add M3U Provider…"
    assert window.add_m3u_provider_action.triggered.callbacks == [window.open_m3u_provider_dialog]
    assert window.add_mag_provider_action.text == "Add MAG/Stalker Provider…"
    assert window.add_mag_provider_action.triggered.callbacks == [window.open_mag_provider_dialog]
    assert window.browse_channels_action.text == "Browse Channels"
    assert window.browse_channels_action.triggered.callbacks == [window.open_channel_browser_dialog]
    assert window.browse_live_categories_action.text == "Browse Live Categories"
    assert window.browse_live_categories_action.triggered.callbacks == [
        window.open_category_browser_dialog
    ]
    assert window.show_epg_action.text == "Show EPG…"
    assert window.show_epg_action.triggered.callbacks == [window.open_epg_grid_dialog]
    assert window.xmltv_guide_action.text == "Configure XMLTV Guide…"
    assert window.xmltv_guide_action.triggered.callbacks == [window.open_xmltv_guide_dialog]
    assert window.show_provider_list_action.text == "Show Registered Providers"
    assert window.show_provider_list_action.triggered.callbacks == [
        window.open_provider_list_dialog
    ]
    assert window.menu_bar.menus[1].title == "Library"
    assert window.menu_bar.menus[1].actions == [
        window.show_favorites_action,
        window.show_history_action,
    ]
    assert window.menu_bar.menus[2].title == "Playback"
    assert window.menu_bar.menus[2].actions == [
        window.pause_playback_action,
        window.resume_playback_action,
        window.stop_playback_action,
        window.start_recording_action,
        window.stop_recording_action,
        window.show_diagnostics_action,
    ]
    assert window.pause_playback_action.text == "Pause"
    assert window.pause_playback_action.triggered.callbacks == [window._schedule_pause_playback]
    assert window.resume_playback_action.text == "Resume"
    assert window.resume_playback_action.triggered.callbacks == [window._schedule_resume_playback]
    assert window.stop_playback_action.text == "Stop"
    assert window.stop_playback_action.triggered.callbacks == [window._schedule_stop_playback]
    assert window.start_recording_action.text == "Start Recording"
    assert window.start_recording_action.triggered.callbacks == [window._schedule_start_recording]
    assert window.stop_recording_action.text == "Stop Recording"
    assert window.stop_recording_action.triggered.callbacks == [window._schedule_stop_recording]
    assert window.show_diagnostics_action.text == "Playback Diagnostics…"
    assert window.show_diagnostics_action.triggered.callbacks == [window.open_playback_diagnostics]
    assert window.menu_bar.actions == [window.settings_action]
    assert window.settings_action.text == "Settings…"
    assert window.settings_action.triggered.callbacks == [window.open_settings_page]


@pytest.mark.asyncio
async def test_main_window_opens_and_loads_theme_settings_dialog() -> None:
    load_theme_preference = FakeThemeLoad(ThemePreference.DARK)
    save_theme_preference = FakeThemeSave()
    window = MainWindow(
        FakePlayer(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakePlayChannel(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        FakeRegistration(),
        load_theme_preference,
        save_theme_preference,
        FakeRegistration(),
        FakeRegistration(),
        FakePlaybackControl(),
        FakePlaybackControl(),
        FakePlaybackControl(),
    )  # type: ignore[arg-type]

    dialog = window.open_settings_dialog()
    await asyncio.sleep(0)

    assert window._active_settings_dialog is dialog
    assert load_theme_preference.calls == 1
    assert dialog.preference_selector.currentData() == ThemePreference.DARK.value
