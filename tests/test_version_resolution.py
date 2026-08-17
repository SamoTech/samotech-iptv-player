from __future__ import annotations

import tomllib
from pathlib import Path

import samotech_iptv

_ROOT = Path(__file__).resolve().parents[1]


def test_package_version_comes_from_authoritative_pyproject() -> None:
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        expected = tomllib.load(handle)["project"]["version"]

    assert samotech_iptv.__version__ == expected
