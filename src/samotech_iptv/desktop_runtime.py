"""Run the Qt/qasync desktop event loop and own runtime lifecycle callbacks."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from samotech_iptv.startup_diagnostics import StartupCheckpoint, StartupDiagnostics

if TYPE_CHECKING:
    from samotech_iptv.desktop_bootstrap import DesktopApplication

__all__ = ["run_desktop_application"]


def run_desktop_application(
    desktop: DesktopApplication,
    *,
    diagnostics: StartupDiagnostics | None = None,
) -> int:
    """Show the desktop window and run its Qt-aware asyncio event loop until quit."""
    from qasync import QEventLoop  # type: ignore[import-untyped]

    event_loop = QEventLoop(desktop.application)
    asyncio.set_event_loop(event_loop)
    if diagnostics is not None:
        diagnostics.checkpoint(StartupCheckpoint.ASYNC_RUNTIME_READY)
    with event_loop:
        try:
            start_callback = getattr(desktop, "start", None)
            if start_callback is not None:
                event_loop.run_until_complete(start_callback())
            desktop.main_window.show()
            if diagnostics is not None:
                diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_SHOWN)
                diagnostics.ready()
            event_loop.run_forever()
        finally:
            close_callback = getattr(desktop, "close", None)
            if close_callback is not None:
                event_loop.run_until_complete(close_callback())
    return 0
