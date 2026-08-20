"""Static safety coverage for the optional Windows diagnostic launcher."""

from __future__ import annotations

from pathlib import Path


def test_debug_launcher_is_optional_local_and_never_accepts_source_secrets() -> None:
    launcher = Path("packaging/SamoTech-Debug.bat").read_text(encoding="utf-8")
    normalized = launcher.casefold()

    assert "samotech_debug_no_pause" in normalized
    assert "samotech_startup_diagnostic_path" in normalized
    assert "--diagnostic" in normalized
    assert "credentials and private urls are never displayed" in normalized
    for forbidden in ("password=", "authorization", "cookie", "proxy", "cors"):
        assert forbidden not in normalized
