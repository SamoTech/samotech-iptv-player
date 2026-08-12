"""Read-only, credential-safe registry adapter for provider summary views."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider import ProviderMetadata
from samotech_iptv.application.ports.provider_catalog_port import ProviderCatalogPort

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

__all__ = ["ProviderCatalogService"]


class ProviderCatalogService(ProviderCatalogPort):
    """Map registry metadata into provider summaries without querying secure stores."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    async def list_providers(self) -> list[ProviderMetadata]:
        """Return registered providers without credentials, tokens, or source secrets."""
        return [
            ProviderMetadata(
                id=metadata.provider_id,
                name=metadata.provider_id,
                type=metadata.provider_type,
                base_url=metadata.base_url,
                is_active=metadata.is_active,
            )
            for metadata in self._registry.list_all()
        ]
