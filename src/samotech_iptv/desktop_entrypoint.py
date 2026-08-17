"""Executable lifecycle owner for the production Qt/libVLC desktop application."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import wave
from typing import TYPE_CHECKING

from samotech_iptv.packaged_runtime import configure_bundled_runtime

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.desktop_bootstrap import DesktopApplication

__all__ = ["main", "run"]

_STARTUP_FAILURE_MESSAGE = "Unable to start SamoTech IPTV Player"
_SMOKE_TEST_ARGUMENT = "--smoke-test"
_PACKAGED_VLC_TEST_ARGUMENT = "--packaged-vlc-test"


async def build_production_desktop_application(
    argv: Sequence[str] | None = None,
) -> DesktopApplication:
    """Lazily import and construct the production desktop graph."""
    from samotech_iptv.desktop_composition import build_production_desktop_application as build

    return await build(argv)


def run_desktop_application(desktop: DesktopApplication) -> int:
    """Lazily import and run the normal Qt/qasync desktop lifecycle."""
    from samotech_iptv.desktop_runtime import run_desktop_application as run_runtime

    return run_runtime(desktop)


async def _run_packaged_vlc_test() -> int:
    """Exercise packaged libVLC with deterministic local silent WAV media."""
    import vlc  # type: ignore[import-untyped]

    with tempfile.TemporaryDirectory(prefix="samotech-vlc-smoke-") as directory:
        media_path = f"{directory}/silence.wav"
        with wave.open(media_path, "wb") as media_file:
            media_file.setnchannels(1)
            media_file.setsampwidth(2)
            media_file.setframerate(8_000)
            media_file.writeframes(b"\\x00\\x00" * 8_000)
        instance = vlc.Instance("--aout=dummy", "--vout=dummy", "--no-video", "--quiet")
        player = instance.media_player_new()
        media = instance.media_new(media_path)
        player.set_media(media)
        if player.play() < 0:
            raise RuntimeError("packaged libVLC could not start synthetic media")
        await asyncio.sleep(0.25)
        player.stop()
        player.release()
        media.release()
        instance.release()
    print("packaged_vlc_smoke=PASS")
    return 0


async def _run_smoke_test(arguments: Sequence[str]) -> int:
    """Initialize the complete desktop graph, process one Qt turn, and close."""
    desktop = await build_production_desktop_application(arguments)
    try:
        start_callback = getattr(desktop, "start", None)
        if start_callback is not None:
            await start_callback()
        desktop.main_window.show()
        process_events = getattr(desktop.application, "processEvents", None)
        if callable(process_events):
            process_events()
    finally:
        close_callback = getattr(desktop, "close", None)
        if close_callback is not None:
            await close_callback()
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    """Build and run the desktop application without exposing startup details."""
    arguments = list(argv) if argv is not None else sys.argv
    configure_bundled_runtime()
    try:
        if _PACKAGED_VLC_TEST_ARGUMENT in arguments:
            return asyncio.run(_run_packaged_vlc_test())
        if _SMOKE_TEST_ARGUMENT in arguments:
            return asyncio.run(_run_smoke_test(arguments))
        desktop = asyncio.run(build_production_desktop_application(arguments))
    except Exception:  # noqa: BLE001
        print(_STARTUP_FAILURE_MESSAGE, file=sys.stderr)
        return 1
    return run_desktop_application(desktop)


def main() -> None:
    """Run the supported ``samotech-iptv`` console entry point."""
    raise SystemExit(run())
