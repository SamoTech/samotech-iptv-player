from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_xtream_vod_series_concurrency_probe() -> None:
    repository = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(repository / "src")
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/xtream_vod_series_concurrency_cases.py",
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[100%]" in result.stdout
