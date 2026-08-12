"""Save the persisted desktop theme preference."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.ports.theme_preference_repository import (
        ThemePreferenceRepository,
    )
    from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

__all__ = ["SaveThemePreference"]


class SaveThemePreference:
    """Persist one validated non-secret desktop theme preference."""

    def __init__(self, repository: ThemePreferenceRepository) -> None:
        self._repository = repository

    async def execute(self, preference: ThemePreference) -> None:
        """Save the selected preference for future desktop launches."""
        await self._repository.save(preference)
