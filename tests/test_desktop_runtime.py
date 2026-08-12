from __future__ import annotations

import asyncio
import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

from samotech_iptv.desktop_runtime import run_desktop_application

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class FakeEventLoop:
    """qasync event-loop double recording desktop runtime lifecycle calls."""

    instances: list[FakeEventLoop] = []

    def __init__(self, application: object) -> None:
        self.application = application
        self.ran_forever = False
        self.cleanup_calls = 0
        type(self).instances.append(self)

    def __enter__(self) -> FakeEventLoop:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def run_forever(self) -> None:
        self.ran_forever = True

    def run_until_complete(self, awaitable: object) -> None:
        self.cleanup_calls += 1
        asyncio.run(awaitable)  # type: ignore[arg-type]


class FakeMainWindow:
    """Desktop main-window double recording visibility requests."""

    def __init__(self) -> None:
        self.show_calls = 0

    def show(self) -> None:
        self.show_calls += 1


def test_runtime_shows_window_and_runs_qasync_loop(monkeypatch: MonkeyPatch) -> None:
    FakeEventLoop.instances.clear()
    qasync = ModuleType("qasync")
    qasync.QEventLoop = FakeEventLoop
    monkeypatch.setitem(sys.modules, "qasync", qasync)
    registered_loops: list[object] = []
    monkeypatch.setattr(asyncio, "set_event_loop", registered_loops.append)
    application = object()
    main_window = FakeMainWindow()
    desktop = SimpleNamespace(application=application, main_window=main_window)

    assert run_desktop_application(desktop) == 0  # type: ignore[arg-type]

    assert main_window.show_calls == 1
    assert len(FakeEventLoop.instances) == 1
    assert FakeEventLoop.instances[0].application is application
    assert FakeEventLoop.instances[0].ran_forever is True
    assert registered_loops == [FakeEventLoop.instances[0]]
    assert FakeEventLoop.instances[0].cleanup_calls == 0


def test_runtime_closes_production_resources_after_qasync_exit(monkeypatch: MonkeyPatch) -> None:
    """The lifecycle owner closes composition-owned resources after the UI loop exits."""
    FakeEventLoop.instances.clear()
    qasync = ModuleType("qasync")
    qasync.QEventLoop = FakeEventLoop
    monkeypatch.setitem(sys.modules, "qasync", qasync)
    monkeypatch.setattr(asyncio, "set_event_loop", lambda _: None)
    close_calls = 0

    async def close() -> None:
        nonlocal close_calls
        close_calls += 1

    desktop = SimpleNamespace(
        application=object(),
        main_window=FakeMainWindow(),
        close=close,
    )

    assert run_desktop_application(desktop) == 0  # type: ignore[arg-type]

    assert close_calls == 1
    assert FakeEventLoop.instances[0].cleanup_calls == 1
