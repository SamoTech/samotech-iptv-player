from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
from samotech_iptv.domain.value_objects.theme_preference import ThemePreference
from samotech_iptv.infrastructure.database.sqlite_theme_preference_repository import (
    SQLiteThemePreferenceRepository,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.asyncio
async def test_sqlite_theme_preference_defaults_to_system_and_persists_selection(
    tmp_path: Path,
) -> None:
    repository = SQLiteThemePreferenceRepository(tmp_path / "settings.sqlite3")

    assert await repository.load() is ThemePreference.SYSTEM

    await repository.save(ThemePreference.DARK)

    assert await repository.load() is ThemePreference.DARK


@pytest.mark.asyncio
async def test_theme_preference_use_cases_delegate_only_validated_preferences(
    tmp_path: Path,
) -> None:
    repository = SQLiteThemePreferenceRepository(tmp_path / "settings.sqlite3")
    save_preference = SaveThemePreference(repository)
    load_preference = LoadThemePreference(repository)

    await save_preference.execute(ThemePreference.LIGHT)

    assert await load_preference.execute() is ThemePreference.LIGHT
