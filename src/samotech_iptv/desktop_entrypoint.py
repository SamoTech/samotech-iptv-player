"""Executable lifecycle owner for the production Qt/libVLC desktop application."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

from samotech_iptv.desktop_composition import build_production_desktop_application
from samotech_iptv.desktop_runtime import run_desktop_application

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["main", "run"]

_STARTUP_FAILURE_MESSAGE = "Unable to start SamoTech IPTV Player"


def run(argv: Sequence[str] | None = None) -> int:
    """Build and run the desktop application without exposing startup details."""
    arguments = list(argv) if argv is not None else sys.argv
    try:
        desktop = asyncio.run(build_production_desktop_application(arguments))
    except Exception:  # noqa: BLE001
        print(_STARTUP_FAILURE_MESSAGE, file=sys.stderr)
        return 1
    return run_desktop_application(desktop)


def main() -> None:
    """Run the supported ``samotech-iptv`` console entry point."""
    raise SystemExit(run())
