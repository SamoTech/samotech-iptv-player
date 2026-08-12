"""Browse-only registered-provider live-category discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.categories import CategoryDTO, LoadCategoriesResponse
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.categories import LoadCategoriesRequest
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["LoadCategories"]

_LOG = get_logger(__name__)


class LoadCategories:
    """Load canonical live categories for one registered provider without playback."""

    def __init__(self, provider_resolver: ProviderResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: LoadCategoriesRequest) -> LoadCategoriesResponse:
        """Resolve a registered category provider and return only safe category data."""
        try:
            provider = self._provider_resolver.resolve_category_provider(request.provider_id)
            categories = await provider.load_live_categories()
        except Exception:  # noqa: BLE001
            _LOG.error("Unable to load registered provider categories")
            return LoadCategoriesResponse(error="Unable to load categories")
        return LoadCategoriesResponse(
            categories=[
                CategoryDTO(
                    id=category.id,
                    name=category.name,
                    provider_id=category.provider_id.value,
                    parent_id=category.parent_id,
                )
                for category in categories
            ]
        )
