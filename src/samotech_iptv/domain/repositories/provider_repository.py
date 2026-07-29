"""ProviderRepository — abstract CRUD contract for Provider aggregates."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from samotech_iptv.domain.entities.provider import Provider
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ProviderRepository"]


class ProviderRepository(ABC):
    """CRUD contract for Provider aggregates."""

    @abstractmethod
    async def get_by_id(self, provider_id: ProviderId) -> Optional[Provider]: ...

    @abstractmethod
    async def list_active(self) -> Sequence[Provider]: ...

    @abstractmethod
    async def save(self, provider: Provider) -> None: ...

    @abstractmethod
    async def delete(self, provider_id: ProviderId) -> bool: ...
