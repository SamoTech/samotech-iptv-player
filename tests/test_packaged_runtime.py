from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

from samotech_iptv import desktop_entrypoint, packaged_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def test_packaged_root_uses_source_project_when_not_frozen() -> None:
    root = packaged_runtime.packaged_root()
    assert (root / "pyproject.toml").is_file()


def test_configure_bundled_runtime_sets_runtime_relative_vlc_paths(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    vlc_root = tmp_path / "vlc"
    plugins = vlc_root / "plugins"
    plugins.mkdir(parents=True)
    (vlc_root / "libvlc.dll").write_bytes(b"synthetic")
    (vlc_root / "libvlccore.dll").write_bytes(b"synthetic")
    handles: list[str] = []

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(
        packaged_runtime.os,
        "add_dll_directory",
        lambda path: handles.append(path) or object(),
        raising=False,
    )
    monkeypatch.delenv("PYTHON_VLC_LIB_PATH", raising=False)
    monkeypatch.delenv("PYTHON_VLC_MODULE_PATH", raising=False)
    monkeypatch.delenv("VLC_PLUGIN_PATH", raising=False)

    result = packaged_runtime.configure_bundled_runtime()

    assert result == vlc_root
    assert (
        packaged_runtime.os.environ["PYTHON_VLC_LIB_PATH"]
        .replace("\\", "/")
        .endswith("vlc/libvlc.dll")
    )
    assert (
        packaged_runtime.os.environ["PYTHON_VLC_MODULE_PATH"]
        .replace("\\", "/")
        .endswith("vlc/plugins")
    )
    assert packaged_runtime.os.environ["VLC_PLUGIN_PATH"].replace("\\", "/").endswith("vlc/plugins")
    assert handles == [str(vlc_root)]


def test_smoke_mode_starts_processes_events_and_closes(monkeypatch: MonkeyPatch) -> None:
    events: list[str] = []
    desktop = SimpleNamespace(
        application=SimpleNamespace(processEvents=lambda: events.append("events")),
        main_window=SimpleNamespace(show=lambda: events.append("show")),
        start=lambda: _record(events, "start"),
        close=lambda: _record(events, "close"),
    )

    async def build(arguments: list[str]) -> object:
        assert arguments == ["samotech-iptv", "--smoke-test"]
        return desktop

    async def smoke_start() -> None:
        events.append("start")

    async def smoke_close() -> None:
        events.append("close")

    desktop.start = smoke_start
    desktop.close = smoke_close
    monkeypatch.setattr(desktop_entrypoint, "configure_bundled_runtime", lambda: None)
    monkeypatch.setattr(desktop_entrypoint, "build_production_desktop_application", build)

    assert desktop_entrypoint.run(["samotech-iptv", "--smoke-test"]) == 0
    assert events == ["start", "show", "events", "close"]


def test_packaged_vlc_mode_dispatches_to_probe(monkeypatch: MonkeyPatch) -> None:
    calls: list[str] = []

    async def packaged_probe() -> int:
        calls.append("probe")
        return 0

    monkeypatch.setattr(desktop_entrypoint, "configure_bundled_runtime", lambda: None)
    monkeypatch.setattr(desktop_entrypoint, "_run_packaged_vlc_test", packaged_probe)

    assert desktop_entrypoint.run(["samotech-iptv", "--packaged-vlc-test"]) == 0
    assert calls == ["probe"]


async def _record(events: list[str], value: str) -> None:
    events.append(value)


def test_source_mode_uses_vlc_runtime_dir_from_arbitrary_cwd(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    runtime_root = tmp_path / "runtime with spaces"
    plugins = runtime_root / "plugins"
    plugins.mkdir(parents=True)
    (runtime_root / "libvlc.dll").write_bytes(b"synthetic")
    (runtime_root / "libvlccore.dll").write_bytes(b"synthetic")
    stale_root = tmp_path / "stale"
    stale_root.mkdir()

    unrelated_cwd = tmp_path / "unrelated-cwd"
    unrelated_cwd.mkdir()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.chdir(unrelated_cwd)
    monkeypatch.setenv("VLC_RUNTIME_DIR", str(runtime_root))
    monkeypatch.setenv("PYTHON_VLC_LIB_PATH", str(stale_root / "libvlc.dll"))
    monkeypatch.setenv("PYTHON_VLC_MODULE_PATH", str(stale_root / "plugins"))
    monkeypatch.setenv("VLC_PLUGIN_PATH", str(stale_root / "plugins"))
    monkeypatch.setattr(packaged_runtime, "_CONFIGURED_VLC_ROOT", None)
    monkeypatch.setattr(
        packaged_runtime.os,
        "add_dll_directory",
        lambda _: object(),
        raising=False,
    )

    result = packaged_runtime.configure_bundled_runtime()

    assert result == runtime_root.resolve()
    assert packaged_runtime.os.environ["PYTHON_VLC_LIB_PATH"] == str(runtime_root / "libvlc.dll")
    assert packaged_runtime.os.environ["PYTHON_VLC_MODULE_PATH"] == str(plugins)
    assert packaged_runtime.os.environ["VLC_PLUGIN_PATH"] == str(plugins)
