"""Run the deterministic Phase 27 large-data measurement probe in isolated real-PySide6 process."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_phase27_large_data_probe() -> None:
    repository = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(repository / "src")
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(repository / "tests/phase27_large_data_probe.py")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["dataset_sizes"] == {
        "categories": 1_000,
        "channels": 10_000,
        "epg_entries": 10_000,
        "movies": 10_000,
        "series": 10_000,
    }
    assert payload["measurements"]["initial_live_render"]["rows"] == 10_000
    assert payload["measurements"]["m3u_parse"]["rows"] == 10_000
    assert payload["measurements"]["epg_render"]["rows"] == 10_000
    assert payload["measurements"]["category_population"]["rows"] == 1_001
    assert payload["measurements"]["movie_render"]["rows"] == 10_000
    assert payload["measurements"]["series_render"]["rows"] == 10_000
    assert payload["provider_search_calls"] == 0
    assert payload["resolver_calls"] == 0
    if os.environ.get("PHASE27_EMIT_METRICS") == "1":
        print(json.dumps(payload, indent=2, sort_keys=True))
