"""Runtime helpers for packaged Windows builds.

The application remains usable from source and on non-Windows platforms. When a
PyInstaller build contains a ``vlc`` directory, this module configures the
python-vlc environment before python-vlc is imported and keeps the Windows DLL
search handle alive for the process lifetime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["configure_bundled_runtime", "packaged_root"]

_DLL_DIRECTORY_HANDLES: list[object] = []
_CONFIGURED_VLC_ROOT: Path | None = None


def packaged_root() -> Path:
    """Return the executable/bundle root without depending on the CWD."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if isinstance(frozen_root, str) and frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[2]


def _windows_dll_directory(path: Path) -> None:
    if sys.platform != "win32" or not hasattr(os, "add_dll_directory"):
        return
    _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(path)))


def _bundled_vlc_root(root: Path) -> Path | None:
    candidates = [root / "vlc", root]
    for candidate in candidates:
        if (candidate / "libvlc.dll").is_file() and (candidate / "libvlccore.dll").is_file():
            return candidate
    return None


def configure_bundled_runtime() -> Path | None:
    """Configure bundled VLC paths before importing :mod:`vlc`.

    Returns the bundled VLC root when present. Source installs and non-Windows
    environments return ``None`` without changing process state.
    """
    if sys.platform != "win32":
        return None
    root = packaged_root()
    vlc_root = _bundled_vlc_root(root)
    if vlc_root is None:
        return None
    plugins = vlc_root / "plugins"
    if not plugins.is_dir():
        return None
    global _CONFIGURED_VLC_ROOT
    if _CONFIGURED_VLC_ROOT == vlc_root:
        return vlc_root

    _windows_dll_directory(vlc_root)
    os.environ.setdefault("PYTHON_VLC_LIB_PATH", str(vlc_root / "libvlc.dll"))
    os.environ.setdefault("PYTHON_VLC_MODULE_PATH", str(plugins))
    os.environ.setdefault("VLC_PLUGIN_PATH", str(plugins))
    _CONFIGURED_VLC_ROOT = vlc_root
    return vlc_root
