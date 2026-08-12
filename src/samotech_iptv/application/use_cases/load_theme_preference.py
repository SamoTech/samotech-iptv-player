"""Load the persisted desktop theme preference."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.theme_preference_repository import (
        ThemePreferenceRepository,
    )
    from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

__all__ = ["LoadThemePreference"]


class LoadThemePreference:
    """Return the non-secret theme preference for desktop composition."""

    def __init__(self, repository: ThemePreferenceRepository) -> None:
        self._repository = repository

    async def execute(self) -> ThemePreference:
        """Load the validated preference with a system-default fallback."""
        return await self._repository.load()
