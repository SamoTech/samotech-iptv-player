"""Integration coverage for browse-only registered Xtream live-category discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.categories import LoadCategoriesRequest
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)
from samotech_iptv.infrastructure.providers.xtream_adapter import register_xtream_with_factory

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext


class FakeHttpClient:
    """Deterministic provider API responder exposing live categories only."""

    async def get_json(self, _: str) -> object:
        return [{"category_id": "news", "category_name": "News"}]


class FakeCredentialStore:
    """Credential boundary retaining a test-only in-memory credential."""

    async def retrieve(self, _: ProviderId) -> Credential:
        return Credential("user", "test-only-password")  # noqa: S106


class FakeContext:
    """Property-compatible context double for registered provider construction."""

    @property
    def http_client(self) -> FakeHttpClient:
        return FakeHttpClient()

    @property
    def credential_store(self) -> FakeCredentialStore:
        return FakeCredentialStore()


@pytest.mark.asyncio
async def test_registered_xtream_live_categories_flow_from_registry_to_safe_dto() -> None:
    """The browse-only workflow uses factory construction and does not invoke playback."""
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="xtream-demo",
            provider_type="xtream",
            base_url="https://portal.example.test",
        )
    )
    factory = ProviderFactory()
    register_xtream_with_factory(factory)
    resolver = ProviderResolutionService(
        registry,
        factory,
        cast("ProviderContext", FakeContext()),
    )

    response = await LoadCategories(resolver).execute(
        LoadCategoriesRequest(provider_id="xtream-demo")
    )

    assert response.error is None
    assert [
        (category.id, category.name, category.provider_id) for category in response.categories
    ] == [("news", "News", "xtream-demo")]
