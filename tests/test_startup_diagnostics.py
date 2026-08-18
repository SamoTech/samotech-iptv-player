from __future__ import annotations

import json
from typing import TYPE_CHECKING

from samotech_iptv.startup_diagnostics import StartupCheckpoint, StartupDiagnostics

if TYPE_CHECKING:
    from pathlib import Path


def test_failure_journal_records_last_stage_and_redacts_sensitive_text(tmp_path: Path) -> None:
    path = tmp_path / "startup-diagnostic.json"
    diagnostics = StartupDiagnostics(path=path)
    diagnostics.checkpoint(StartupCheckpoint.RUNTIME_INITIALIZED)
    diagnostics.checkpoint(
        StartupCheckpoint.PATHS_INITIALIZED,
        details={"bundled_vlc_root": r"C:\Program Files\VLC"},
    )

    diagnostics.fail(
        RuntimeError(
            r"Could not load token=SAMOSTART_TOKEN from https://user:password@example.invalid/libvlc.dll"
        ),
        reason="vlc_discovery_failed",
        exit_code=1,
    )

    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["status"] == "failed"
    assert state["last_successful_stage"] == "PATHS_INITIALIZED"
    assert state["completed_stages"][-1] == "PATHS_INITIALIZED"
    assert state["exit_reason"] == "vlc_discovery_failed"
    assert state["exit_code"] == 1
    assert "SAMOSTART_TOKEN" not in path.read_text(encoding="utf-8")
    assert "user:password" not in path.read_text(encoding="utf-8")
    assert "https://example.invalid/libvlc.dll" in state["failure_message"]
    assert "failure_traceback" in state
    assert "RuntimeError" in state["failure_traceback"]
    assert state["diagnostic_path"] == str(path)
    assert "runtime_directory" in state["environment"]
    assert "vlc_runtime_directory" in state["environment"]


def test_non_diagnostic_ready_state_is_removed(tmp_path: Path) -> None:
    path = tmp_path / "startup-diagnostic.json"
    diagnostics = StartupDiagnostics(path=path)
    assert path.is_file()

    diagnostics.ready(details={"mode": "smoke_test"})

    assert not path.exists()


def test_diagnostic_mode_retains_ready_state(tmp_path: Path) -> None:
    path = tmp_path / "startup-diagnostic.json"
    diagnostics = StartupDiagnostics(diagnostic_mode=True, path=path)
    diagnostics.checkpoint(StartupCheckpoint.VLC_READY)
    diagnostics.checkpoint(StartupCheckpoint.MAIN_WINDOW_SHOWN)

    diagnostics.ready(details={"mode": "diagnostic"})

    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["status"] == "ready"
    assert state["last_successful_stage"] == "APPLICATION_READY"
    assert "VLC_READY" in state["completed_stages"]
    assert "MAIN_WINDOW_SHOWN" in state["completed_stages"]
    assert "APPLICATION_READY" in state["completed_stages"]
    assert state["exit_code"] == 0
