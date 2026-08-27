"""Executable lifecycle owner for the production Qt/libVLC desktop application."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import wave
from typing import TYPE_CHECKING

from samotech_iptv.packaged_runtime import configure_bundled_runtime
from samotech_iptv.startup_diagnostics import StartupCheckpoint, StartupDiagnostics

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.desktop_bootstrap import DesktopApplication

__all__ = ["main", "run"]

_STARTUP_FAILURE_MESSAGE = "Unable to start SamoTech IPTV Player"
_SMOKE_TEST_ARGUMENT = "--smoke-test"
_PACKAGED_VLC_TEST_ARGUMENT = "--packaged-vlc-test"
_DIAGNOSTIC_ARGUMENT = "--diagnostic"
_QT_ONLY_TEST_ARGUMENT = "--qt-only-test"


async def build_production_desktop_application(
    argv: Sequence[str] | None = None,
) -> DesktopApplication:
    """Lazily import and construct the production desktop graph."""
    from samotech_iptv.desktop_composition import build_production_desktop_application as build

    return await build(argv)


def run_desktop_application(
    desktop: DesktopApplication,
    *,
    diagnostics: StartupDiagnostics | None = None,
) -> int:
    """Lazily import and run the normal Qt/qasync desktop lifecycle."""
    from samotech_iptv.desktop_runtime import run_desktop_application as run_runtime

    return run_runtime(desktop, diagnostics=diagnostics)


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


async def _run_qt_only_test(
    arguments: Sequence[str],
    diagnostics: StartupDiagnostics,
) -> int:
    """Initialize Qt and create a minimal window without constructing libVLC."""
    from PySide6.QtWidgets import QApplication, QMainWindow

    application = QApplication.instance() or QApplication(list(arguments))
    diagnostics.checkpoint(StartupCheckpoint.QT_INITIALIZED)
    diagnostics.checkpoint(StartupCheckpoint.QT_PLATFORM_READY)
    window = QMainWindow()
    window.setWindowTitle("SamoTech IPTV Player Qt diagnostic")
    window.resize(640, 360)
    diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_CREATED)
    window.show()
    diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_SHOWN)
    process_events = getattr(application, "processEvents", None)
    if callable(process_events):
        process_events()
    window.close()
    diagnostics.checkpoint(StartupCheckpoint.APPLICATION_READY)
    return 0


async def _run_smoke_test(
    arguments: Sequence[str],
    diagnostics: StartupDiagnostics,
) -> int:
    """Initialize the complete desktop graph, process one Qt turn, and close."""
    diagnostics.checkpoint(StartupCheckpoint.CONFIG_INITIALIZED)
    diagnostics.checkpoint(StartupCheckpoint.VLC_DISCOVERY_STARTED)
    desktop = await build_production_desktop_application(arguments)
    diagnostics.checkpoint(StartupCheckpoint.VLC_READY)
    diagnostics.checkpoint(StartupCheckpoint.SERVICES_INITIALIZED)
    diagnostics.checkpoint(StartupCheckpoint.QT_INITIALIZED)
    diagnostics.checkpoint(StartupCheckpoint.QT_PLATFORM_READY)
    diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_CREATED)
    try:
        start_callback = getattr(desktop, "start", None)
        if start_callback is not None:
            await start_callback()
        desktop.main_window.show()
        diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_SHOWN)
        process_events = getattr(desktop.application, "processEvents", None)
        if callable(process_events):
            process_events()
    finally:
        close_callback = getattr(desktop, "close", None)
        if close_callback is not None:
            await close_callback()
    diagnostics.checkpoint(StartupCheckpoint.APPLICATION_READY)
    return 0


def _exit_code_from_exception(exc: BaseException) -> int:
    if isinstance(exc, SystemExit) and isinstance(exc.code, int):
        return exc.code
    return 1


def run(argv: Sequence[str] | None = None) -> int:
    """Build and run the desktop application with durable failure diagnostics."""
    arguments = list(argv) if argv is not None else sys.argv
    diagnostics = StartupDiagnostics(diagnostic_mode=_DIAGNOSTIC_ARGUMENT in arguments)
    try:
        diagnostics.checkpoint(StartupCheckpoint.RUNTIME_INITIALIZED)
        runtime_root = configure_bundled_runtime()
        diagnostics.checkpoint(
            StartupCheckpoint.PATHS_INITIALIZED,
            details={"bundled_vlc_root": str(runtime_root) if runtime_root else "not_found"},
        )
        diagnostics.checkpoint(StartupCheckpoint.LOGGING_INITIALIZED)
        if _QT_ONLY_TEST_ARGUMENT in arguments:
            result = asyncio.run(_run_qt_only_test(arguments, diagnostics))
            diagnostics.ready(details={"mode": "qt_only_test"})
            return result
        if _PACKAGED_VLC_TEST_ARGUMENT in arguments:
            diagnostics.checkpoint(StartupCheckpoint.VLC_DISCOVERY_STARTED)
            result = asyncio.run(_run_packaged_vlc_test())
            diagnostics.ready(
                stage=StartupCheckpoint.VLC_READY,
                details={"mode": "packaged_vlc_test"},
            )
            return result
        if _SMOKE_TEST_ARGUMENT in arguments:
            result = asyncio.run(_run_smoke_test(arguments, diagnostics))
            diagnostics.ready(details={"mode": "smoke_test"})
            return result
        diagnostics.checkpoint(StartupCheckpoint.CONFIG_INITIALIZED)
        diagnostics.checkpoint(StartupCheckpoint.VLC_DISCOVERY_STARTED)
        desktop = asyncio.run(build_production_desktop_application(arguments))
        diagnostics.checkpoint(StartupCheckpoint.VLC_READY)
        diagnostics.checkpoint(StartupCheckpoint.SERVICES_INITIALIZED)
        diagnostics.checkpoint(StartupCheckpoint.QT_INITIALIZED)
        diagnostics.checkpoint(StartupCheckpoint.QT_PLATFORM_READY)
        diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_CREATED)
        return run_desktop_application(desktop, diagnostics=diagnostics)
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        exit_code = _exit_code_from_exception(exc)
        diagnostics.fail(
            exc,
            reason="startup_exception",
            exit_code=exit_code,
            details={"mode": "diagnostic" if _DIAGNOSTIC_ARGUMENT in arguments else "normal"},
        )
        print(
            f"{_STARTUP_FAILURE_MESSAGE}.\n"
            f"Startup phase: {diagnostics.last_successful_stage.value}\n"
            "Details: A required runtime component could not be initialized.\n"
            f"Diagnostic log: {diagnostics.path}",
            file=sys.stderr,
        )
        return exit_code


def main() -> None:
    """Run the supported ``samotech-iptv`` console entry point."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
