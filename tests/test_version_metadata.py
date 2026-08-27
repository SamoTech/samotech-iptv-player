"""Ensure every legitimate current-version source remains synchronized for releases."""

from __future__ import annotations

import tomllib
from pathlib import Path

from samotech_iptv.core.constants import APP_VERSION


def test_runtime_version_matches_authoritative_project_metadata() -> None:
    with Path("pyproject.toml").open("rb") as file:
        project_version = tomllib.load(file)["project"]["version"]

    assert project_version == "0.1.7"
    assert APP_VERSION == project_version


def test_current_status_records_the_same_package_version() -> None:
    status = Path("PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "**Package version:** `0.1.7`" in status
