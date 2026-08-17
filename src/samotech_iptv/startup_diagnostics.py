"""Durable, redacted startup checkpoints for frozen and source execution."""

from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
import time
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv import __version__
from samotech_iptv.core.safe_logging import safe_label, sanitize_exception

if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = [
    "StartupCheckpoint",
    "StartupDiagnostics",
    "startup_diagnostics_path",
]


class StartupCheckpoint(StrEnum):
    """Ordered milestones in the desktop startup lifecycle."""

    BOOTLOADER_STARTED = "BOOTLOADER_STARTED"
    RUNTIME_INITIALIZED = "RUNTIME_INITIALIZED"
    PATHS_INITIALIZED = "PATHS_INITIALIZED"
    LOGGING_INITIALIZED = "LOGGING_INITIALIZED"
    CONFIG_INITIALIZED = "CONFIG_INITIALIZED"
    QT_INITIALIZED = "QT_INITIALIZED"
    QT_PLATFORM_READY = "QT_PLATFORM_READY"
    ASYNC_RUNTIME_READY = "ASYNC_RUNTIME_READY"
    VLC_DISCOVERY_STARTED = "VLC_DISCOVERY_STARTED"
    VLC_READY = "VLC_READY"
    SERVICES_INITIALIZED = "SERVICES_INITIALIZED"
    MAIN_WINDOW_CREATED = "MAIN_WINDOW_CREATED"
    MAIN_WINDOW_SHOWN = "MAIN_WINDOW_SHOWN"
    APPLICATION_READY = "APPLICATION_READY"


_CHECKPOINT_ORDER = {stage: position for position, stage in enumerate(StartupCheckpoint)}


def startup_diagnostics_path() -> Path:
    """Return a stable path without relying on the current directory."""
    configured_path = os.environ.get("SAMOTECH_STARTUP_DIAGNOSTIC_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local_app_data:
        return Path(local_app_data) / "SamoTech" / "IPTV Player" / "startup-diagnostic.json"
    return Path.home() / ".samotech_iptv" / "startup-diagnostic.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_path(value: object) -> str:
    return safe_label(value, limit=400)


def _environment_snapshot() -> dict[str, object]:
    frozen_root = getattr(sys, "_MEIPASS", None)
    return {
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "frozen": isinstance(frozen_root, str) and bool(frozen_root),
        "executable": _safe_path(sys.executable),
        "cwd": _safe_path(os.getcwd()),
        "temp": _safe_path(tempfile.gettempdir()),
        "tmp": _safe_path(os.environ.get("TMP", "")),
        "temp_env": _safe_path(os.environ.get("TEMP", "")),
        "appdata": _safe_path(os.environ.get("APPDATA", "")),
        "localappdata": _safe_path(os.environ.get("LOCALAPPDATA", "")),
        "meipass": _safe_path(frozen_root or ""),
        "platform": _safe_path(platform.platform()),
        "platform_version": _safe_path(platform.version()),
        "architecture": _safe_path(platform.machine()),
    }


class StartupDiagnostics:
    """Write atomic startup state and retain it only when requested or needed."""

    def __init__(
        self,
        *,
        diagnostic_mode: bool = False,
        path: Path | None = None,
    ) -> None:
        self.path = path or startup_diagnostics_path()
        self.diagnostic_mode = diagnostic_mode
        self._started = time.monotonic()
        self._last_stage = StartupCheckpoint.BOOTLOADER_STARTED
        self._state: dict[str, object] = {
            "schema_version": 1,
            "application_version": __version__,
            "started_utc": _utc_now(),
            "status": "in_progress",
            "last_successful_stage": self._last_stage.value,
            "completed_stages": [self._last_stage.value],
            "environment": _environment_snapshot(),
        }
        self.checkpoint(self._last_stage)

    @property
    def last_successful_stage(self) -> StartupCheckpoint:
        """Return the last checkpoint committed by the startup path."""
        return self._last_stage

    @property
    def state(self) -> Mapping[str, object]:
        """Return the current safe in-memory snapshot for tests and summaries."""
        return dict(self._state)

    def checkpoint(
        self,
        stage: StartupCheckpoint,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Atomically persist a successful startup checkpoint."""
        if _CHECKPOINT_ORDER[stage] < _CHECKPOINT_ORDER[self._last_stage]:
            return
        self._last_stage = stage
        self._state["last_successful_stage"] = stage.value
        completed_stages = self._state.setdefault("completed_stages", [])
        if isinstance(completed_stages, list) and stage.value not in completed_stages:
            completed_stages.append(stage.value)
        self._state["checkpoint_utc"] = _utc_now()
        if details:
            self._state["details"] = {
                str(key): safe_label(value, limit=400) for key, value in details.items()
            }
        self._write()

    def fail(
        self,
        exc: BaseException,
        *,
        reason: str,
        exit_code: int,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Persist a sanitized failure record and retain it for user diagnosis."""
        self._state.update(
            {
                "status": "failed",
                "exit_reason": safe_label(reason),
                "exit_code": exit_code,
                "failure_type": type(exc).__name__,
                "failure_message": sanitize_exception(exc),
                "elapsed_seconds": round(time.monotonic() - self._started, 3),
                "finished_utc": _utc_now(),
            }
        )
        if details:
            self._state["failure_details"] = {
                str(key): safe_label(value, limit=400) for key, value in details.items()
            }
        self._write()

    def ready(
        self,
        *,
        stage: StartupCheckpoint = StartupCheckpoint.APPLICATION_READY,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Record successful mode readiness, retaining reports in diagnostic mode."""
        self.checkpoint(stage)
        self._state.update(
            {
                "status": "ready",
                "last_successful_stage": self._last_stage.value,
                "exit_code": 0,
                "elapsed_seconds": round(time.monotonic() - self._started, 3),
                "finished_utc": _utc_now(),
            }
        )
        if details:
            self._state["ready_details"] = {
                str(key): safe_label(value, limit=400) for key, value in details.items()
            }
        if self.diagnostic_mode:
            self._write()
        else:
            self._remove()

    def incomplete(self, *, reason: str, exit_code: int) -> None:
        """Record a clean process termination that never reached readiness."""
        self.fail(
            RuntimeError("startup did not reach application readiness"),
            reason=reason,
            exit_code=exit_code,
        )

    def _write(self) -> None:
        """Write JSON through a flushed temporary file and atomic replacement."""
        fallback = Path(tempfile.gettempdir()) / "SamoTech" / "IPTV Player" / self.path.name
        candidates = [self.path] if fallback == self.path else [self.path, fallback]
        for candidate in candidates:
            temporary: Path | None = None
            try:
                candidate.parent.mkdir(parents=True, exist_ok=True)
                temporary = candidate.with_name(f".{candidate.name}.tmp")
                with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                    json.dump(self._state, handle, ensure_ascii=True, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, candidate)
                self.path = candidate
                return
            except OSError:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass

    def _remove(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass
