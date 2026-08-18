# -*- mode: python ; coding: utf-8 -*-
"""Forensic PyInstaller variants; production spec remains unchanged."""

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE
from PyInstaller.building.build_main import Analysis, PYZ
from PyInstaller.utils.hooks import collect_submodules

from samotech_iptv import __version__

project_root = Path(SPEC).resolve().parents[1]
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

mode = os.environ.get("SAMOTECH_FORENSIC_BUILD_MODE", "onefile").strip().lower()
valid_modes = {"onedir", "onefile", "debug-bootloader", "debug-all"}
if mode not in valid_modes:
    raise SystemExit(f"SAMOTECH_FORENSIC_BUILD_MODE must be one of {sorted(valid_modes)}")

runtime_tmpdir = os.environ.get("SAMOTECH_FORENSIC_RUNTIME_TMPDIR") or None
is_onedir = mode == "onedir"
is_debug = mode in {"debug-bootloader", "debug-all"}
debug_bootloader = is_debug
console = is_debug
python_options = [("v", None, "OPTION")] if mode == "debug-all" else []

vlc_binaries = [(str(path), "vlc") for path in vlc_root.glob("*.dll")]
vlc_datas = [(str(plugins_root), "vlc/plugins")]
application_datas = [(str(project_root / "pyproject.toml"), ".")]
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
version_info_path = project_root / "build" / f"forensic_version_info_{mode}.txt"
version_info_path.parent.mkdir(parents=True, exist_ok=True)
version_info_path.write_text(
    f"""VSVersionInfo(

    ffi=FixedFileInfo(
        filevers={version_parts},
        prodvers={version_parts},
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'040904B0',
                [
                    StringStruct(u'CompanyName', u'SamoTech'),
                    StringStruct(u'FileDescription', u'SamoTech IPTV Player forensic {mode}'),
                    StringStruct(u'FileVersion', u'{__version__}'),
                    StringStruct(u'InternalName', u'SamoTech-IPTV-Player-Windows-x64-forensic-{mode}'),
                    StringStruct(u'OriginalFilename', u'SamoTech-IPTV-Player-Windows-x64-forensic-{mode}.exe'),
                    StringStruct(u'ProductName', u'SamoTech IPTV Player'),
                    StringStruct(u'ProductVersion', u'{__version__}'),
                ],
            )
        ]),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])]),
    ],
)
""",
    encoding="utf-8",
)

analysis = Analysis(
    [str(project_root / "src" / "samotech_iptv" / "desktop_entrypoint.py")],
    pathex=[str(project_root / "src"), str(project_root)],
    binaries=vlc_binaries,
    datas=vlc_datas + application_datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "samotech_runtime_hook.py")],
    excludes=["tkinter", "matplotlib", "notebook", "IPython"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
name = f"SamoTech-IPTV-Player-Windows-x64-forensic-{mode}"
if is_onedir:
    exe = EXE(
        pyz,
        analysis.scripts,
        *python_options,
        exclude_binaries=True,
        name=name,
        debug=debug_bootloader,
        strip=False,
        upx=False,
        runtime_tmpdir=runtime_tmpdir,
        console=console,
        disable_windowed_traceback=not is_debug,
        version=str(version_info_path),
    )
    coll = COLLECT(
        exe,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=False,
        name=name,
    )
else:
    exe = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        *python_options,
        [],
        name=name,
        debug=debug_bootloader,
        strip=False,
        upx=False,
        runtime_tmpdir=runtime_tmpdir,
        console=console,
        disable_windowed_traceback=not is_debug,
        version=str(version_info_path),
    )
