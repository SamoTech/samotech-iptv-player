"""Resolve the package version from the authoritative project metadata."""

from __future__ import annotations

import sys
import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path


def _pyproject_candidates() -> tuple[Path, ...]:
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "pyproject.toml")
    candidates.append(Path(__file__).resolve().parents[2] / "pyproject.toml")
    return tuple(candidates)


def _read_authoritative_version() -> str | None:
    for path in _pyproject_candidates():
        if not path.is_file():
            continue
        with path.open("rb") as file:
            value = tomllib.load(file).get("project", {}).get("version")
        if isinstance(value, str) and value:
            return value
    return None


def _resolve_version() -> str:
    metadata_version = _read_authoritative_version()
    if metadata_version is not None:
        return metadata_version
    try:
        return package_version("samotech-iptv-player")
    except PackageNotFoundError as exc:
        raise RuntimeError("Unable to resolve SamoTech IPTV Player version") from exc


__version__: str = _resolve_version()

__all__ = ["__version__"]
