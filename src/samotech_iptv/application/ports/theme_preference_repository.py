"""Persistence boundary for the user’s desktop theme preference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

__all__ = ["ThemePreferenceRepository"]


class ThemePreferenceRepository(ABC):
    """Load and save one non-secret desktop theme preference."""

    @abstractmethod
    async def load(self) -> ThemePreference:
        """Return the saved preference or the system default."""
        ...

    @abstractmethod
    async def save(self, preference: ThemePreference) -> None:
        """Persist one validated theme preference."""
        ...
