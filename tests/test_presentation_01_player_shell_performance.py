"""Run the real-PySide6 large-catalogue probe in an isolated interpreter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_player_shell_39753_channel_performance_probe() -> None:
    repository = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(repository / "src")
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(repository / "tests/player_shell_performance_probe.py")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["total_records"] == 39_753
    assert payload["model_row_count_after_initial_replace"] == 39_753
    assert payload["first_middle_last_identity"] == [
        "channel-00001",
        "channel-19877",
        "channel-39753",
    ]
    assert payload["empty_row_count"] == 0
    assert payload["content_model_records"] == 5_000
    assert payload["content_model_row_count"] == 5_000
    assert payload["content_first_middle_last_identity"] == [
        "content-00001",
        "content-02501",
        "content-05000",
    ]
    assert list(payload["dynamic_catalogue_results"]) == [
        "0",
        "1",
        "100",
        "1000",
        "5000",
        "39753",
        "100000",
    ]
    assert payload["dynamic_catalogue_results"]["0"]["clear_search_rows"] == 0
    assert payload["dynamic_catalogue_results"]["100000"]["clear_search_rows"] == 100_000
    assert payload["resolver_calls"] == 0
    assert payload["provider_search_calls"] == 0
    assert payload["catalogue_reload_calls"] == 0
