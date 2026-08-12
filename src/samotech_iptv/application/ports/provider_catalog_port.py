"""Read-only provider summary boundary for presentation views."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.provider import ProviderMetadata

__all__ = ["ProviderCatalogPort"]


class ProviderCatalogPort(ABC):
    """Expose non-secret registered-provider summaries to application use cases."""

    @abstractmethod
    async def list_providers(self) -> Sequence[ProviderMetadata]:
        """Return all provider summaries without credentials, tokens, or raw secrets."""
        ...
