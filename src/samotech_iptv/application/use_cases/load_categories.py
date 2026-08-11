"""LoadCategories use-case (stub — implemented in Phase B)."""

from __future__ import annotations

from samotech_iptv.application.dtos import LoadCategoriesRequest, LoadCategoriesResponse


class LoadCategories:
    """Load content categories from a provider.

    .. note::
        Full implementation depends on ``ProviderPort.load_categories``
        which is added in Phase B.
    """

    async def execute(self, request: LoadCategoriesRequest) -> LoadCategoriesResponse:
        return LoadCategoriesResponse(error="LoadCategories not yet implemented — Phase B")
