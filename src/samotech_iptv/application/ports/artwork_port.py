"""Provider-scoped artwork loading boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

__all__ = ["ArtworkPort", "ArtworkRequest", "ArtworkRole"]


class ArtworkRole(StrEnum):
    """Supported artwork presentation roles."""

    POSTER = "poster"
    BACKDROP = "backdrop"


@dataclass(frozen=True)
class ArtworkRequest:
    """Identify one provider-scoped artwork fetch without exposing credentials."""

    provider_id: str
    content_id: str
    role: ArtworkRole
    url: str


class ArtworkPort(ABC):
    """Load bounded image bytes through the application-owned artwork boundary."""

    @abstractmethod
    async def load(self, request: ArtworkRequest) -> bytes | None:
        """Return valid image bytes or ``None`` for invalid/failed artwork."""
        ...

    @abstractmethod
    def clear_provider(self, provider_id: str) -> None:
        """Invalidate cached artwork belonging to one provider."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Invalidate all cached artwork."""
        ...
