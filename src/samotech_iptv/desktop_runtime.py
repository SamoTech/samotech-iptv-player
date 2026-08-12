"""Supported Qt and asyncio runtime for the desktop application shell."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.desktop_bootstrap import DesktopApplication

__all__ = ["run_desktop_application"]


def run_desktop_application(desktop: DesktopApplication) -> int:
    """Show the desktop window and run its Qt-aware asyncio event loop until quit."""
    from qasync import QEventLoop  # type: ignore[import-not-found]

    event_loop = QEventLoop(desktop.application)
    asyncio.set_event_loop(event_loop)
    desktop.main_window.show()
    with event_loop:
        try:
            event_loop.run_forever()
        finally:
            close_callback = getattr(desktop, "close", None)
            if close_callback is not None:
                event_loop.run_until_complete(close_callback())
    return 0
