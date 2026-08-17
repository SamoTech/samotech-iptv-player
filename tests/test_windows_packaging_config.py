from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_spec_has_explicit_bundled_vlc_and_runtime_hook() -> None:
    spec = (_ROOT / "samotech-iptv-player.spec").read_text(encoding="utf-8")
    assert "VLC_RUNTIME_DIR" in spec
    assert "libvlc.dll" in spec
    assert "libvlccore.dll" in spec
    assert "plugins" in spec
    assert "samotech_runtime_hook.py" in spec
    assert "SamoTech-IPTV-Player-Windows-x64" in spec
    assert "collect-all" not in spec


def test_windows_workflow_keeps_release_gates_blocking() -> None:
    workflow = (_ROOT / ".github/workflows/windows-portable-build.yml").read_text(encoding="utf-8")
    assert "continue-on-error" not in workflow
    assert "tests/vlc_native_lifecycle_probe.py" in workflow
    assert "--packaged-vlc-test" in workflow
    assert "--smoke-test" in workflow
    assert "SHA256SUMS.txt" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "softprops/action-gh-release@v2" in workflow


def test_windows_build_script_preserves_downloaded_vlc_runtime() -> None:
    script = (_ROOT / "scripts/build_windows.ps1").read_text(encoding="utf-8")
    assert "build\\pyinstaller" in script or 'Join-Path "build" "pyinstaller"' in script
    assert 'Remove-Item -Recurse -Force "build"' not in script
    assert "VLC_RUNTIME_DIR" in script
    assert "PyInstaller" in script


def test_pinned_windows_packaging_requirements_are_present() -> None:
    requirements = (_ROOT / "packaging/windows-build-requirements.txt").read_text(encoding="utf-8")
    for requirement in (
        "PyInstaller==6.22.1",
        "PySide6==6.11.1",
        "python-vlc==3.0.21203",
        "qasync==0.28.0",
    ):
        assert requirement in requirements
