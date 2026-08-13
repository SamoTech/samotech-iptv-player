"""Persistence boundary for registered provider XMLTV source bindings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["XMLTVBindingRepository"]


class XMLTVBindingRepository(ABC):
    """Persist non-secret local XMLTV sources and explicit channel mappings."""

    @abstractmethod
    async def initialise(self) -> None:
        """Create backing storage when it does not yet exist."""

    @abstractmethod
    async def load(self, provider_id: ProviderId) -> XMLTVBinding | None:
        """Return one provider binding or ``None`` when it has not been configured."""

    @abstractmethod
    async def save(self, binding: XMLTVBinding) -> None:
        """Create or replace one provider's XMLTV binding atomically."""

    @abstractmethod
    async def delete(self, provider_id: ProviderId) -> bool:
        """Delete one provider binding and report whether it existed."""
