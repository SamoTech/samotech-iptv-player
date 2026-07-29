"""FavoriteRepository — abstract CRUD contract for Favorite records."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from samotech_iptv.domain.entities.favorite import Favorite

__all__ = ["FavoriteRepository"]


class FavoriteRepository(ABC):
    """CRUD contract for Favorite records."""

    @abstractmethod
    async def list_all(self) -> Sequence[Favorite]: ...

    @abstractmethod
    async def save(self, favorite: Favorite) -> None: ...

    @abstractmethod
    async def delete(self, favorite_id: str) -> bool: ...
