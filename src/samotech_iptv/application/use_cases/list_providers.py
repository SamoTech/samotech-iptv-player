"""List credential-safe provider summaries for presentation views."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.provider import ProviderMetadata
    from samotech_iptv.application.ports.provider_catalog_port import ProviderCatalogPort

__all__ = ["ListProviders"]


class ListProviders:
    """Load safe registered-provider summaries through the read-only catalog boundary."""

    def __init__(self, provider_catalog: ProviderCatalogPort) -> None:
        self._provider_catalog = provider_catalog

    async def execute(self) -> Sequence[ProviderMetadata]:
        """Return provider summaries without credentials, tokens, or raw secret sources."""
        return await self._provider_catalog.list_providers()
