# -*- mode: python ; coding: utf-8 -*-
"""Reproducible Windows PyInstaller configuration for SamoTech IPTV Player."""

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.building.build_main import Analysis, EXE, PYZ
from PyInstaller.utils.hooks import collect_submodules

from samotech_iptv import __version__

project_root = Path(SPEC).resolve().parent
vlc_root_value = os.environ.get("VLC_RUNTIME_DIR")
if not vlc_root_value:
    raise SystemExit("VLC_RUNTIME_DIR must point to the pinned Windows VLC runtime")
vlc_root = Path(vlc_root_value).resolve()
required_vlc_files = (vlc_root / "libvlc.dll", vlc_root / "libvlccore.dll")
plugins_root = vlc_root / "plugins"
if not all(path.is_file() for path in required_vlc_files):
    raise SystemExit("VLC_RUNTIME_DIR is missing libvlc.dll or libvlccore.dll")
if not plugins_root.is_dir():
    raise SystemExit("VLC_RUNTIME_DIR is missing the plugins directory")

vlc_binaries = [(str(path), "vlc") for path in vlc_root.glob("*.dll")]
vlc_datas = [(str(plugins_root), "vlc/plugins")]
for directory_name in ("lua", "locale"):
    directory = vlc_root / directory_name
    if directory.is_dir():
        vlc_datas.append((str(directory), f"vlc/{directory_name}"))

hiddenimports = [
    "providers.base",
    "providers.registry",
    "samotech_iptv.packaged_runtime",
]
hiddenimports.extend(collect_submodules("providers"))

version_parts = tuple(int(part) for part in __version__.split("."))
version_parts = (version_parts + (0, 0, 0, 0))[:4]
version_info_path = project_root / "build" / "version_info.txt"
version_info_path.parent.mkdir(parents=True, exist_ok=True)
version_info_path.write_text(
    f'''VSVersionInfo(\n\n    ffi=FixedFileInfo(\n        filevers={version_parts},\n        prodvers={version_parts},\n        mask=0x3f,\n        flags=0x0,\n        OS=0x40004,\n        fileType=0x1,\n        subtype=0x0,\n        date=(0, 0),\n    ),\n    kids=[\n        StringFileInfo([\n            StringTable(\n                u\'040904B0\',\n                [\n                    StringStruct(u\'CompanyName\', u\'SamoTech\'),\n                    StringStruct(u\'FileDescription\', u\'SamoTech IPTV Player\'),\n                    StringStruct(u\'FileVersion\', u\'{__version__}\'),\n                    StringStruct(u\'InternalName\', u\'SamoTech-IPTV-Player-Windows-x64\'),\n                    StringStruct(u\'OriginalFilename\', u\'SamoTech-IPTV-Player-Windows-x64.exe\'),\n                    StringStruct(u\'ProductName\', u\'SamoTech IPTV Player\'),\n                    StringStruct(u\'ProductVersion\', u\'{__version__}\'),\n                ],\n            )\n        ]),\n        VarFileInfo([VarStruct(u\'Translation\', [1033, 1200])]),\n    ],\n)\n''',
    encoding="utf-8",
)

analysis = Analysis(
    [str(project_root / "src" / "samotech_iptv" / "desktop_entrypoint.py")],
    pathex=[str(project_root / "src"), str(project_root)],
    binaries=vlc_binaries,
    datas=vlc_datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "samotech_runtime_hook.py")],
    excludes=["tkinter", "matplotlib", "notebook", "IPython"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="SamoTech-IPTV-Player-Windows-x64",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    version=str(version_info_path),
)
